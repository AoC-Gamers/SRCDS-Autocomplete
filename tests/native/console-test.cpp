// The translation unit below is the canonical, unmodified product source.
#include "../../extension/src/extension.cpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <link.h>

ISmmAPI api;
ISmmAPI *g_SMAPI=&api;
GameConfs configs;
MemoryUtils memory;
SMUtils utilities;
ICvar cvars;
static link_map libraryMap{};
static int openFailures=0,openCalls=0,closeCalls=0;
extern "C" void *__wrap_dlopen(const char *,int) {
    ++openCalls;
    if(openFailures>0) { --openFailures;return nullptr; }
    return &libraryMap;
}
extern "C" int __wrap_dlclose(void *) { ++closeCalls;return 0; }
CTextConsole::~CTextConsole() = default;
class Console:public CTextConsole {
public:
    std::string output;
    int width=80;
    Console() {
        memset(m_szConsoleText,0,sizeof(m_szConsoleText));
        m_nConsoleTextLen=0;m_nCursorPosition=0;m_nInputLine=4;m_nBrowseLine=0;
    }
    void Input(const char *text) {
        snprintf(m_szConsoleText,sizeof(m_szConsoleText),"%s",text);
        m_nConsoleTextLen=strlen(m_szConsoleText);output.clear();
    }
    bool Init() override { return true; }
    void ShutDown() override {}
    void Print(char *) override {}
    void SetTitle(char *) override {}
    void SetStatusLine(char *) override {}
    void UpdateStatus() override {}
    void Echo(const char *msg,int length=0) override { if(length) output.append(msg,length);else output+=msg; }
    char *GetLine() override { return m_szConsoleText; }
    int GetWidth() override { return width; }
    void SetVisible(bool value) override { m_ConsoleVisible=value; }
    bool IsVisible() override { return m_ConsoleVisible; }
};
static void AssertContains(const CUtlVector<const char *> &values,const char *expected) {
    for(int i=0;i<values.Count();i++) if(!strcmp(values[i],expected)) return;
    assert(false && "missing expected suggestion");
}
static void ManualCases() {
    struct Case { const char *partial;const char *match; };
    for(auto test:{Case{"meta v","meta version"},Case{"sm e","sm exts"},Case{"sm exts l","sm exts list"},Case{"sm plugins r","sm plugins reload"}}) {
        CUtlVector<const char *> matches;CUtlVector<int> kinds;
        assert(GetManualRootSuggestions(test.partial,matches,kinds));
        assert(matches.Count()==kinds.Count());AssertContains(matches,test.match);
        for(int i=0;i<kinds.Count();i++) assert(kinds[i]==MatchKind_Manual);
    }
    for(const char *text:{"sm","status ","sm unknown ","sm exts xyz","sm plugins xyz","metax a"}) {
        CUtlVector<const char *> matches;CUtlVector<int> kinds;
        assert(!GetManualRootSuggestions(text,matches,kinds));
    }
    assert(!strcmp(GetMatchKindLabel(MatchKind_Command),"cmd"));
    assert(!strcmp(GetMatchKindLabel(MatchKind_ConVar),"cvar"));
    assert(!strcmp(GetMatchKindLabel(MatchKind_Manual),"manual"));
    assert(!strcmp(GetMatchKindLabel(99),"?"));
    CUtlVector<const char *> matches;matches.AddToTail("Zulu");matches.AddToTail("alpha");
    SortMatches(matches);assert(!strcmp(matches[0],"alpha"));
}
static void FileCases(const std::filesystem::path &root) {
    api.baseDirectory=root.string();
    std::filesystem::create_directories(root/"addons/sourcemod/plugins");
    std::filesystem::create_directories(root/"addons/sourcemod/extensions");
    for(const char *name:{"alpha.smx","ALPINE.SMX","ignore.txt","x"}) std::ofstream(root/"addons/sourcemod/plugins"/name)<<"fixture";
    std::ofstream(root/"addons/sourcemod/extensions/autocomplete.ext.2.l4d2.so")<<"fixture";
    for(const char *prefix:{"sm plugins load ","sm plugins reload ","sm plugins unload "}) {
        CUtlVector<const char *> matches;CUtlVector<int> kinds;
        const std::string input=std::string(prefix)+"al";
        assert(GetManualFileSuggestions(input.c_str(),matches,kinds));assert(matches.Count()==2);
        AssertContains(matches,(std::string(prefix)+"alpha.smx").c_str());
    }
    for(const char *prefix:{"sm exts load ","sm exts reload ","sm exts unload "}) {
        CUtlVector<const char *> matches;CUtlVector<int> kinds;
        assert(GetManualFileSuggestions(prefix,matches,kinds));assert(matches.Count()==1);
    }
    CUtlVector<const char *> matches;CUtlVector<int> kinds;
    assert(!GetManualFileSuggestions("sm other ",matches,kinds));
    AddFileSuggestionsFromDirectory("load ","load ","missing",".smx",matches,kinds);assert(matches.Count()==0);
    for(int i=0;i<300;i++) std::ofstream(root/"addons/sourcemod/plugins"/("bulk"+std::to_string(i)+".smx"))<<"fixture";
    assert(GetManualFileSuggestions("sm plugins load bulk",matches,kinds));assert(matches.Count()==256);
}
static void ConsoleCases() {
    ConCommand status("status"),start("start"),stop("stop"),hidden("secret",FCVAR_HIDDEN),dev("secret_dev",FCVAR_DEVELOPMENTONLY),change("changelevel"),plain("plain");
    plain.canComplete=false;change.suggestions={"changelevel c1", "changelevel c2"};
    cvars.commands={&status,&start,&stop,&hidden,&dev,&change,&plain,&sm_autocomplete_debug};
    api.cvars=&cvars;icvar=&cvars;
    Console console;
    console.Input("statu");HandleReceiveTab(&console);assert(!strcmp(console.m_szConsoleText,"status "));
    assert(console.output=="s ");assert(console.m_nCursorPosition==7 && console.m_nBrowseLine==4);
    console.Input("no_such_command");HandleReceiveTab(&console);assert(console.output.empty());
    console.Input("");HandleReceiveTab(&console);assert(console.output.empty());
    console.m_nConsoleTextLen=-1;HandleReceiveTab(&console);assert(console.output.empty());
    console.m_nConsoleTextLen=MAX_CONSOLE_TEXTLEN;assert(!InsertConsoleText(&console,"x",false));
    console.Input("sta");console.width=1;HandleReceiveTab(&console);assert(console.output.find("[cmd] start")!=std::string::npos);
    console.Input("s");sm_autocomplete_max_results.SetValue(2);assert(DoAutocompletion(&console,"s",1)==2);sm_autocomplete_max_results.SetValue(32);
    console.Input("changelevel c");assert(DoAutocompletion(&console,console.m_szConsoleText,console.m_nConsoleTextLen)==2);
    assert(!FindAutoCompleteCommandFromPartial("missing arg"));assert(!FindAutoCompleteCommandFromPartial("plain arg"));
    CUtlVector<const char *> matches;CUtlVector<int> kinds;
    GetSuggestions("secret",6,matches,kinds);assert(matches.Count()==0);
    GetSuggestions("sm_auto",7,matches,kinds);assert(matches.Count()==1 && kinds[0]==MatchKind_ConVar);
    matches.Purge();kinds.Purge();GetSuggestions("unknown arg",11,matches,kinds);assert(matches.Count()==0);
    change.suggestions={"x"};console.Input("changelevel long");assert(DoAutocompletion(&console,console.m_szConsoleText,console.m_nConsoleTextLen)==0);
    console.Input(std::string(255,'a').c_str());assert(InsertConsoleText(&console,"suffix",false));assert(console.m_nConsoleTextLen==255);
    console.Input("abc");memcpy(console.m_szConsoleText+3,"stale",6);assert(NormalizeConsoleTextState(&console));assert(!strcmp(console.m_szConsoleText,"abc"));
    matches.Purge();kinds.Purge();matches.AddToTail("alpha one");matches.AddToTail("alpha two");kinds.AddToTail(0);kinds.AddToTail(1);
    console.Input("al");console.width=80;PrintSuggestionTable(&console,matches,kinds,2);assert(!strcmp(console.m_szConsoleText,"alpha "));
    sm_autocomplete_debug.SetValue(1);console.Input("meta v");HandleReceiveTab(&console);assert(!utilities.messages.empty());sm_autocomplete_debug.SetValue(0);
    // The actual detour body uses the provider's member-callback calling path.
    console.Input("statu");reinterpret_cast<DetourReceiveTabClass *>(&console)->DetourReceiveTab();assert(!strcmp(console.m_szConsoleText,"status "));
    cvars.commands.clear();
}
static void LifecycleCases() {
    char error[256]{};api.cvars=&cvars;
    assert(g_AutoCompleteHook.SDK_OnMetamodLoad(&api,error,sizeof(error),false));
    api.cvars=nullptr;assert(!g_AutoCompleteHook.SDK_OnMetamodLoad(&api,error,sizeof(error),false));
    assert(!g_AutoCompleteHook.SDK_OnLoad(error,sizeof(error),false));api.cvars=&cvars;
    configs.load=false;assert(!g_AutoCompleteHook.SDK_OnLoad(error,sizeof(error),false));configs.load=true;
    assert(configs.loads==configs.closes);
    openFailures=2;assert(!g_AutoCompleteHook.SDK_OnLoad(error,sizeof(error),false));assert(configs.loads==configs.closes);
    void *handle=nullptr;openFailures=2;assert(!ResolveDedicatedLibrary(error,sizeof(error),&handle));
    openFailures=1;assert(ResolveDedicatedLibrary(error,sizeof(error),&handle));ReleaseDedicatedLibrary(handle);ReleaseDedicatedLibrary(nullptr);
    configs.config.value=nullptr;assert(!GetAddressFromKeyValues(&libraryMap,&configs.config,"key"));
    configs.config.value="";assert(!GetAddressFromKeyValues(&libraryMap,&configs.config,"key"));
    configs.config.value="\\x41\\x00";libraryMap.l_addr=0x8000;
    assert(GetAddressFromKeyValues(&libraryMap,&configs.config,"key")==memory.result);
    assert(memory.pattern==std::string("A\0",2) && memory.base==reinterpret_cast<void *>(0x8000));
    configs.config.value="@ReceiveTab";memory.result=nullptr;assert(!EnableReceiveTabDetour(&libraryMap,&configs.config,error,sizeof(error)));
    memory.result=reinterpret_cast<void *>(0x1234);CDetourManager::create=false;assert(!EnableReceiveTabDetour(&libraryMap,&configs.config,error,sizeof(error)));
    CDetourManager::create=true;assert(g_AutoCompleteHook.SDK_OnLoad(error,sizeof(error),false));assert(receiveTab->enabled);
    assert(registrations==1 && configs.closes>=1 && closeCalls>=2);
    ConCommand command("test");assert(g_AutoCompleteHook.RegisterConCommandBase(&command));
    api.allowRegistration=false;assert(!g_AutoCompleteHook.RegisterConCommandBase(&command));api.allowRegistration=true;
    g_AutoCompleteHook.SDK_OnUnload();assert(CDetourManager::detour.destroyed && unregistrations==1);
    receiveTab=nullptr;g_AutoCompleteHook.SDK_OnUnload();assert(unregistrations==2);
    memory.result=nullptr;assert(!g_AutoCompleteHook.SDK_OnLoad(error,sizeof(error),false));memory.result=reinterpret_cast<void *>(0x1234);
    assert(configs.loads==configs.closes);
}
int main(int argc,char **argv) {
    assert(argc==2);gameconfs=&configs;memutils=&memory;smutils=&utilities;
    ManualCases();FileCases(argv[1]);ConsoleCases();LifecycleCases();
    puts("console: canonical product scenarios passed with controlled providers");
}
