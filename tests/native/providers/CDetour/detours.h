#pragma once
class CDetour {
public:
    bool enabled=false,destroyed=false;
    void EnableDetour() { enabled=true; }
    void Destroy() { destroyed=true; }
};
class CDetourManager {
public:
    static inline bool create=true;
    static inline CDetour detour;
    static inline int initializes=0;
    static void Init(void *,void *) { ++initializes; }
    static CDetour *Create() { return create ? &detour : nullptr; }
};
#define DETOUR_DECL_MEMBER0(name,ret) class name##Class { public: ret name(); }; ret name##Class::name()
#define DETOUR_CREATE_MEMBER(name,address) CDetourManager::Create()
