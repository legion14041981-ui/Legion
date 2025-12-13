"""Performance Tests - JSON Serialization"""

import pytest
import json
import orjson
import time
from legion.infrastructure.performance import ORJSONResponse


class TestSerializationPerformance:
    """Test JSON serialization performance improvements"""
    
    def generate_large_dataset(self, size: int = 10000):
        """Generate large test dataset"""
        return [
            {
                "id": i,
                "title": f"Task {i}",
                "description": "A" * 200,
                "metadata": {"key1": "value1", "key2": "value2"},
                "tags": ["tag1", "tag2", "tag3"]
            }
            for i in range(size)
        ]
    
    def test_orjson_vs_standard_json(self):
        """Compare orjson vs standard json performance"""
        data = self.generate_large_dataset(1000)
        
        # Standard json
        start = time.perf_counter()
        for _ in range(100):
            json.dumps(data)
        standard_time = time.perf_counter() - start
        
        # orjson
        start = time.perf_counter()
        for _ in range(100):
            orjson.dumps(data)
        orjson_time = time.perf_counter() - start
        
        # orjson should be 5-10x faster
        speedup = standard_time / orjson_time
        assert speedup >= 5.0, f"orjson speedup: {speedup:.1f}x (expected >= 5x)"
    
    @pytest.mark.benchmark
    def test_orjson_response_benchmark(self, benchmark):
        """Benchmark ORJSONResponse rendering"""
        data = self.generate_large_dataset(1000)
        response = ORJSONResponse(content=data)
        
        result = benchmark(response.render, data)
        
        # Should complete in < 10ms
        assert result < 0.010, f"Rendering took {result*1000:.2f}ms (expected < 10ms)"
