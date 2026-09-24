#include "pipeline_snapshot.hpp"
#include <iostream>
#include <cstring>
using namespace cyrs;
using namespace reshade::api;
int main() {
    try {
        std::vector<uint8_t> vs{1,2,3,4}, ps{5,6,7,8};
        shader_desc shaders[2]{}; shaders[0].code = vs.data(); shaders[0].code_size = vs.size(); shaders[1].code = ps.data(); shaders[1].code_size = ps.size();
        char semantic[] = "POSITION";
        input_element input{}; input.semantic = semantic; input.offset = 12;
        format format_value = format::r8g8b8a8_unorm;
        blend_desc blend{}; blend.blend_enable[0] = true;
        pipeline_subobject objects[] = {{pipeline_subobject_type::vertex_shader,1,&shaders[0]}, {pipeline_subobject_type::pixel_shader,1,&shaders[1]},
            {pipeline_subobject_type::input_layout,1,&input}, {pipeline_subobject_type::render_target_formats,1,&format_value}, {pipeline_subobject_type::blend_state,1,&blend}};
        PipelineSnapshot snapshot(5, objects, {123});
        vs.assign(4,0); ps.assign(4,0); semantic[0] = 'X'; input.offset = 99; blend.blend_enable[0] = false;
        shader_desc replacement{}; uint8_t new_ps[] = {9,9}; replacement.code = new_ps; replacement.code_size = 2;
        auto copy = snapshot.variant(replacement);
        require(snapshot.layout.handle == 123, "Root signature identity changed");
        auto vertex = static_cast<shader_desc *>(copy[0].data);
        require(static_cast<const uint8_t *>(vertex->code)[0] == 1, "Vertex bytecode was not deeply copied");
        require(copy[1].data == &replacement, "Pixel shader was not replaced");
        auto element = static_cast<input_element *>(copy[2].data);
        require(std::strcmp(element->semantic,"POSITION") == 0 && element->offset == 12, "Input layout not preserved");
        require(static_cast<blend_desc *>(copy[4].data)->blend_enable[0], "Blend state not preserved");
        bool refused = false; objects[4].type = pipeline_subobject_type::libraries;
        try { PipelineSnapshot invalid(5, objects, {123}); } catch (...) { refused = true; }
        require(refused, "Unknown pipeline subobject silently dropped");
        std::cout << "Pipeline lifetime, signature identity, bytecode and render-state tests passed\n";
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
