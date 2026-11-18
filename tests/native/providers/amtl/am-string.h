#pragma once
namespace ke {
inline void SafeStrcpy(char *out,size_t length,const char *text) { if(length) snprintf(out,length,"%s",text); }
template<class... Args> void SafeSprintf(char *out,size_t length,const char *format,Args... args) { if(length) snprintf(out,length,format,args...); }
inline void SafeVsprintf(char *out,size_t length,const char *format,va_list args) { if(length) vsnprintf(out,length,format,args); }
}
