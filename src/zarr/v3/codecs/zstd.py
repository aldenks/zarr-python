from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
)

from attr import field, frozen
from zstandard import ZstdCompressor, ZstdDecompressor

from zarr.v3.abc.codec import BytesBytesCodec
from zarr.v3.codecs.registry import register_codec
from zarr.v3.common import BytesLike, to_thread

if TYPE_CHECKING:
    from zarr.v3.metadata import ArraySpec, CodecMetadata, RuntimeConfiguration


@frozen
class ZstdCodecConfigurationMetadata:
    level: int = 0
    checksum: bool = False


@frozen
class ZstdCodecMetadata:
    configuration: ZstdCodecConfigurationMetadata
    name: Literal["zstd"] = field(default="zstd", init=False)


@frozen
class ZstdCodec(BytesBytesCodec):
    configuration: ZstdCodecConfigurationMetadata
    is_fixed_size = True

    @classmethod
    def from_metadata(cls, codec_metadata: CodecMetadata) -> ZstdCodec:
        assert isinstance(codec_metadata, ZstdCodecMetadata)
        return cls(configuration=codec_metadata.configuration)

    @classmethod
    def get_metadata_class(cls) -> type[ZstdCodecMetadata]:
        return ZstdCodecMetadata

    def _compress(self, data: bytes) -> bytes:
        ctx = ZstdCompressor(
            level=self.configuration.level, write_checksum=self.configuration.checksum
        )
        return ctx.compress(data)

    def _decompress(self, data: bytes) -> bytes:
        ctx = ZstdDecompressor()
        return ctx.decompress(data)

    async def decode(
        self,
        chunk_bytes: bytes,
        _chunk_spec: ArraySpec,
        _runtime_configuration: RuntimeConfiguration,
    ) -> BytesLike:
        return await to_thread(self._decompress, chunk_bytes)

    async def encode(
        self,
        chunk_bytes: bytes,
        _chunk_spec: ArraySpec,
        _runtime_configuration: RuntimeConfiguration,
    ) -> Optional[BytesLike]:
        return await to_thread(self._compress, chunk_bytes)

    def compute_encoded_size(self, _input_byte_length: int, _chunk_spec: ArraySpec) -> int:
        raise NotImplementedError


register_codec("zstd", ZstdCodec)
