// A STANDING IN FOR UNREAL'S CoreMinimal.h, AND IT DECLARES NOTHING.
//
// WHY IT EXISTS. ue-probe/Source/LedgerProbe/Public/Perception.h includes
// CoreMinimal.h, as every header inside an Unreal module does, and Unreal
// does not exist in the container that writes this code. The ported
// simulation under LedgerCore uses no Unreal type at all, deliberately and
// by the standing rule from 25 August: measurement arithmetic and the
// decisions live where the tests run, because this project's top layer does
// not compile locally and anything written there ships UNRUN.
//
// So the g++ test compiles the port with this directory on the include path
// and gets an empty header where Unreal's would be. It is EMPTY on purpose:
// anything in the port that reaches for a real Unreal type fails to compile
// here, loudly, rather than being quietly satisfied by a stub. This shim can
// only ever hide a dependency by declaring one, and it declares none.
//
// IT IS NOT ON UNREAL'S INCLUDE PATH. The module build never sees this
// directory, so the engine build still gets the engine's own header. Putting
// a file of this name beside Perception.h would have shadowed the real one,
// which is why it lives here instead.
#pragma once
