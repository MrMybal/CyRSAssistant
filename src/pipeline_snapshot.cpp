#include "pipeline_snapshot.hpp"
#include <cstring>

namespace cyrs {
using namespace reshade::api;
PipelineSnapshot::PipelineSnapshot(uint32_t count, const pipeline_subobject *source, pipeline_layout root) : layout(root) {
    require(count > 0 && count <= 64 && source, "Invalid graphics pipeline description");
    objects.reserve(count);
    for (uint32_t i = 0; i < count; ++i) {
        auto object = source[i];
        if (!object.count) { objects.push_back(object); continue; }
        require(object.data, "Missing graphics pipeline subobject");
        switch (object.type) {
        case pipeline_subobject_type::vertex_shader:
        case pipeline_subobject_type::hull_shader:
        case pipeline_subobject_type::domain_shader:
        case pipeline_subobject_type::geometry_shader:
        case pipeline_subobject_type::pixel_shader: {
            require(object.count == 1, "Shader arrays are unsupported in graphics pipeline snapshots");
            auto desc = copy(static_cast<const shader_desc *>(object.data), 1);
            require(desc->spec_constants == 0 && desc->code && desc->code_size, "Unsupported shader description");
            desc->code = copy(static_cast<const uint8_t *>(desc->code), desc->code_size);
            if (desc->entry_point) desc->entry_point = copy(desc->entry_point, std::strlen(desc->entry_point) + 1);
            object.data = desc;
            if (object.type == pipeline_subobject_type::pixel_shader) {
                require(pixel_index == SIZE_MAX, "Multiple pixel shader subobjects"); pixel_index = objects.size();
            }
            break;
        }
        case pipeline_subobject_type::input_layout: {
            auto elements = copy(static_cast<const input_element *>(object.data), object.count);
            for (uint32_t j = 0; j < object.count; ++j) if (elements[j].semantic)
                elements[j].semantic = copy(elements[j].semantic, std::strlen(elements[j].semantic) + 1);
            object.data = elements; break;
        }
#define CYRS_COPY_CASE(name, type) case pipeline_subobject_type::name: object.data = copy(static_cast<const type *>(object.data), object.count); break
        CYRS_COPY_CASE(stream_output_state, stream_output_desc);
        CYRS_COPY_CASE(blend_state, blend_desc);
        CYRS_COPY_CASE(rasterizer_state, rasterizer_desc);
        CYRS_COPY_CASE(depth_stencil_state, depth_stencil_desc);
        CYRS_COPY_CASE(primitive_topology, primitive_topology);
        CYRS_COPY_CASE(depth_stencil_format, format);
        CYRS_COPY_CASE(render_target_formats, format);
        CYRS_COPY_CASE(sample_mask, uint32_t);
        CYRS_COPY_CASE(sample_count, uint32_t);
        CYRS_COPY_CASE(viewport_count, uint32_t);
        CYRS_COPY_CASE(dynamic_pipeline_states, dynamic_state);
        CYRS_COPY_CASE(flags, pipeline_flags);
#undef CYRS_COPY_CASE
        default: throw std::runtime_error("Graphics pipeline contains an unsupported subobject: " + std::to_string(static_cast<uint32_t>(object.type)));
        }
        objects.push_back(object);
        require(bytes <= 4 * 1024 * 1024, "Graphics pipeline exceeds 4 MiB capture budget");
    }
    require(pixel_index != SIZE_MAX, "Pipeline has no pixel shader");
    // Layout lifetime is retained by the D3D12 caller after successful capture.
}
std::vector<pipeline_subobject> PipelineSnapshot::variant(shader_desc &pixel) const {
    auto result = objects;
    result[pixel_index].data = &pixel;
    return result;
}
}
