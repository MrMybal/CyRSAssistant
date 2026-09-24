#pragma once
#include <reshade.hpp>
#include <unknwn.h>
#include "protocol.hpp"
#include <memory>
#include <vector>
#include <string>

namespace cyrs {
// Own every pointer-bearing payload exposed by init_pipeline. Unknown subobjects
// are rejected, never silently omitted from a reconstructed graphics pipeline.
class PipelineSnapshot {
    std::vector<std::shared_ptr<void>> storage;
    std::vector<reshade::api::pipeline_subobject> objects;
    size_t pixel_index = SIZE_MAX;
    template<class T> T *copy(const T *source, size_t count) {
        require(count <= 1024 * 1024 / sizeof(T), "Pipeline subobject exceeds capture budget");
        auto values = std::make_shared<std::vector<T>>(source, source + count);
        auto ptr = values->data(); bytes += count * sizeof(T); storage.push_back(values); return ptr;
    }
public:
    size_t bytes = 0;
    reshade::api::pipeline_layout layout{};
    std::shared_ptr<IUnknown> root_signature;
    PipelineSnapshot(uint32_t count, const reshade::api::pipeline_subobject *source, reshade::api::pipeline_layout root);
    std::vector<reshade::api::pipeline_subobject> variant(reshade::api::shader_desc &pixel) const;
};
}
