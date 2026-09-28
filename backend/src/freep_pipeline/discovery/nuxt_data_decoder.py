"""Decodes Nuxt's `__NUXT_DATA__` payload format ("devalue").

Freep server-renders a Nuxt app and embeds its full page data — including
every job currently listed, regardless of segment — as a flat JSON array
in <script id="__NUXT_DATA__">. Objects and lists in this array reference
each other by integer index instead of nesting inline, to deduplicate
repeated values. This decoder resolves those indices back into plain
nested Python values.
"""

from __future__ import annotations

_REACTIVE_WRAPPER_TAGS = ("ShallowReactive", "Reactive", "Ref")


class NuxtDataDecoder:
    """Resolves a devalue-encoded array (as parsed from __NUXT_DATA__) into
    plain Python values."""

    def decode(self, raw_array: list) -> object:
        self._raw_array = raw_array
        self._resolved: dict[int, object] = {}
        return self._resolve(0)

    def _resolve(self, index: int) -> object:
        if index in self._resolved:
            return self._resolved[index]

        value = self._raw_array[index]
        self._resolved[index] = None  # guard against reference cycles

        if isinstance(value, list):
            out = self._resolve_list(value)
        elif isinstance(value, dict):
            out = self._resolve_dict(value)
        else:
            out = value

        self._resolved[index] = out
        return out

    def _resolve_list(self, value: list) -> object:
        if len(value) == 2 and value[0] in _REACTIVE_WRAPPER_TAGS:
            return self._resolve(value[1])
        return [self._resolve(v) if isinstance(v, int) else v for v in value]

    def _resolve_dict(self, value: dict) -> dict:
        return {k: (self._resolve(v) if isinstance(v, int) else v) for k, v in value.items()}
