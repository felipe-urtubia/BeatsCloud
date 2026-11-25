"""
Entrega privada de audio local con soporte HTTP Range.

La autorizacion ocurre en full_stream_api antes de llamar
a esta funcion. No se utiliza para archivos R2.
"""
import mimetypes
import re

from django.http import HttpResponse, StreamingHttpResponse
from django.utils.http import content_disposition_header


CHUNK_SIZE = 64 * 1024


def serve_local_track_audio(request, track):
    file_field = track.track
    size = file_field.size
    filename = file_field.name.rsplit("/", 1)[-1]
    mime = (
        mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    start = 0
    end = size - 1
    status = 200

    range_header = request.headers.get("Range", "").strip()

    if range_header:
        match = re.fullmatch(
            r"bytes=(\d*)-(\d*)",
            range_header,
            flags=re.IGNORECASE,
        )

        valid = bool(
            match and (match.group(1) or match.group(2))
        )

        if valid:
            first, last = match.groups()

            if first:
                start = int(first)
                end = int(last) if last else size - 1
                end = min(end, size - 1)
            else:
                suffix = int(last)
                if suffix <= 0:
                    valid = False
                else:
                    start = max(0, size - suffix)
                    end = size - 1

            if start >= size or start > end:
                valid = False

        if not valid:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            response["Accept-Ranges"] = "bytes"
            response["Cache-Control"] = "private, no-store"
            return response

        status = 206

    length = max(0, end - start + 1)

    def chunks():
        remaining = length

        with file_field.open("rb") as audio_file:
            audio_file.seek(start)

            while remaining > 0:
                block = audio_file.read(
                    min(CHUNK_SIZE, remaining)
                )

                if not block:
                    break

                remaining -= len(block)
                yield block

    response = StreamingHttpResponse(
        chunks(),
        status=status,
        content_type=mime,
    )

    response["Content-Length"] = str(length)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = (
        content_disposition_header(False, filename)
    )

    if status == 206:
        response["Content-Range"] = (
            f"bytes {start}-{end}/{size}"
        )

    return response
