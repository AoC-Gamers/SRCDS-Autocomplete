#pragma once
// Controlled SDK providers for execution of the unchanged canonical extension.
// These are not packaged and do not claim binary compatibility with SRCDS.
#include <algorithm>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <strings.h>
#include <vector>
#include "hex-string.h"
#define SOURCE_ENGINE 15
#define SE_LEFT4DEAD2 15
#define SE_ORANGEBOX 3
#define SMEXT_CONF_METAMOD
#define KEY_SUFFIX "_lin"
#define CVAR_INTERFACE_VERSION "VEngineCvar004"
#define FCVAR_NOTIFY 1
#define FCVAR_DEVELOPMENTONLY 2
#define FCVAR_HIDDEN 4
#define PLATFORM_MAX_PATH 4096
#define stricmp strcasecmp
#define Q_strnicmp strncasecmp

template<class T> class CUtlVector {
    std::vector<T> values;
public:
    int Count() const { return static_cast<int>(values.size()); }
    void AddToTail(const T &value) { values.push_back(value); }
    void Remove(int index) { values.erase(values.begin()+index); }
    void Purge() { values.clear(); }
    T &operator[](int index) { return values.at(index); }
    const T &operator[](int index) const { return values.at(index); }
};
class CUtlString {
    std::string value;
public:
    CUtlString(const char *text):value(text) {}
    const char *String() const { return value.c_str(); }
};
class ConCommandBase {
    std::string name;
    bool command;
    int flags;
public:
    ConCommandBase(const char *n,bool cmd=true,int f=0):name(n),command(cmd),flags(f) {}
    virtual ~ConCommandBase() = default;
    const char *GetName() const { return name.c_str(); }
    bool IsFlagSet(int f) const { return flags & f; }
    bool IsCommand() const { return command; }
};
class ConCommand:public ConCommandBase {
public:
    bool canComplete=true;
    std::vector<std::string> suggestions;
    explicit ConCommand(const char *name,int flags=0):ConCommandBase(name,true,flags) {}
    bool CanAutoComplete() const { return canComplete; }
    int AutoCompleteSuggest(const char *,CUtlVector<CUtlString> &out) {
        for (const auto &s:suggestions) out.AddToTail(CUtlString(s.c_str()));
        return static_cast<int>(suggestions.size());
    }
};
class ConVar:public ConCommandBase {
    int value;
public:
    ConVar(const char *name,const char *v,int,const char *,bool,float,bool,float):ConCommandBase(name,false),value(atoi(v)) {}
    int GetInt() const { return value; }
    bool GetBool() const { return value!=0; }
    void SetValue(int v) { value=v; }
};
class ICvar {
public:
    std::vector<ConCommandBase *> commands;
    ConCommand *FindCommand(const char *name) {
        for (auto *c:commands) if(c->IsCommand() && !strcmp(name,c->GetName())) return static_cast<ConCommand *>(c);
        return nullptr;
    }
    class Iterator {
        ICvar *owner; size_t index=0;
    public:
        explicit Iterator(ICvar *c):owner(c) {}
        void SetFirst() { index=0; }
        bool IsValid() const { return index<owner->commands.size(); }
        void Next() { ++index; }
        ConCommandBase *Get() { return owner->commands.at(index); }
    };
};
inline ICvar *g_pCVar=nullptr;
class ISmmAPI {
public:
    ICvar *cvars=nullptr;
    std::string baseDirectory;
    bool allowRegistration=true;
    void *GetEngineFactory() { return nullptr; }
    void *VInterfaceMatch(void *,const char *) { return cvars; }
    const char *GetBaseDir() { return baseDirectory.c_str(); }
};
#define GET_V_IFACE_CURRENT(factory,var,type,name) \
    var=static_cast<type *>(ismm->VInterfaceMatch(ismm->factory(),name)); \
    if(!var) { if(error && maxlen) snprintf(error,maxlen,"Could not find interface: %s",name); return false; }
#define META_REGCVAR(var) (g_SMAPI->allowRegistration && (var)!=nullptr)
inline int registrations=0,unregistrations=0;
inline void ConVar_Register(int,void *) { ++registrations; }
inline void ConVar_Unregister() { ++unregistrations; }
class IGameConfig {
public:
    const char *value="@ReceiveTab";
    const char *GetKeyValue(const char *) { return value; }
};
class GameConfs {
public:
    IGameConfig config;
    bool load=true;
    int closes=0;
    bool LoadGameConfigFile(const char *,IGameConfig **out,char *error,size_t size) {
        if(!load) { snprintf(error,size,"provider failure"); return false; }
        *out=&config;return true;
    }
    void CloseGameConfigFile(IGameConfig *) { ++closes; }
};
class MemoryUtils {
public:
    void *result=reinterpret_cast<void *>(0x1234);
    void *base=nullptr;
    std::string pattern;
    void *ResolveSymbol(void *handle,const char *) { base=handle;return result; }
    void *FindPattern(const void *handle,const char *bytes,size_t length) {
        base=const_cast<void *>(handle);pattern.assign(bytes,length);return result;
    }
};
class SMUtils {
public:
    std::vector<std::string> messages;
    void *GetScriptingEngine() { return nullptr; }
    void LogMessage(void *,const char *format,const char *text) {
        char buffer[1024];snprintf(buffer,sizeof(buffer),format,text);messages.emplace_back(buffer);
    }
};
inline GameConfs *gameconfs=nullptr;
inline MemoryUtils *memutils=nullptr;
inline SMUtils *smutils=nullptr;
inline void *myself=nullptr;
class AutoCompleteHook {
public:
    bool SDK_OnLoad(char *,size_t,bool);
    void SDK_OnUnload();
    bool SDK_OnMetamodLoad(ISmmAPI *,char *,size_t,bool);
    bool RegisterConCommandBase(ConCommandBase *);
};
#define SMEXT_LINK(pointer) static_assert(true,"controlled SDK entrypoint")
