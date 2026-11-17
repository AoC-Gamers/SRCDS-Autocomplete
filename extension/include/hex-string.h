#ifndef SRCDS_AUTOCOMPLETE_HEX_STRING_H
#define SRCDS_AUTOCOMPLETE_HEX_STRING_H

#include <stddef.h>

// Decode complete \xHH escapes, leaving malformed/truncated escapes literal.
// Writes at most maxlength bytes, returns their count, and does not append NUL.
size_t UTIL_DecodeHexString(unsigned char *buffer, size_t maxlength, const char *hexstr);

#endif
