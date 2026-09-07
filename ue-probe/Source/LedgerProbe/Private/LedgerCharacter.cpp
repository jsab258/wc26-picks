#include "LedgerCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputCoreTypes.h"

ALedgerCharacter::ALedgerCharacter()
{
	// EXPLICIT RATHER THAN INHERITED. ACharacter's own default capsule
	// (34x88) has never been named in this codebase before this file, so
	// it is set here rather than trusted. VignetteShot.cpp's interactive
	// player start lifts the spawn 1.1 m above the pavement precisely so
	// it does not have to match this number exactly: gravity settles the
	// rest on the first tick either way.
	GetCapsuleComponent()->InitCapsuleSize(34.0f, 88.0f);

	// THE BODY TURNS TO FACE WHERE IT WALKS, NOT WHERE THE MOUSE LOOKS.
	// The camera boom below reads the controller's rotation on its own
	// (bUsePawnControlRotation), so the two rotations are independent:
	// looking around does not spin the capsule, which is what makes a
	// spring-arm camera behave like a camera and not a turret bolted to
	// the player's forehead.
	bUseControllerRotationYaw = false;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;

	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->bOrientRotationToMovement = true;
		Movement->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
	}

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 350.0f;
	CameraBoom->bUsePawnControlRotation = true;
	// THE ARM PULLS IN RATHER THAN CLIPPING THROUGH A WALL. This street has
	// narrow gaps between pieces and a camera three and a half metres
	// behind the player would otherwise pass straight through a shopfront.
	// bDoCollisionTest is the spring arm's own default; named here so a
	// later reader does not have to open engine source to learn it is on.
	CameraBoom->bDoCollisionTest = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;
}

void ALedgerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	check(PlayerInputComponent);

	PlayerInputComponent->BindAxisKey(EKeys::W, this, &ALedgerCharacter::MoveForward);
	PlayerInputComponent->BindAxisKey(EKeys::S, this, &ALedgerCharacter::MoveBackward);
	PlayerInputComponent->BindAxisKey(EKeys::D, this, &ALedgerCharacter::MoveRight);
	PlayerInputComponent->BindAxisKey(EKeys::A, this, &ALedgerCharacter::MoveLeft);
	// TURN HAS NO SIGN FLIP AND LOOK-UP DOES. This is Epic's own long
	// standing DefaultInput.ini convention (Turn from MouseX at scale 1,
	// LookUp from MouseY at scale -1), reproduced here in code because
	// this project has no DefaultInput.ini to read it from.
	PlayerInputComponent->BindAxisKey(EKeys::MouseX, this, &ALedgerCharacter::LookYaw);
	PlayerInputComponent->BindAxisKey(EKeys::MouseY, this, &ALedgerCharacter::LookPitch);
}

void ALedgerCharacter::MoveForward(float Value)  { AddMovementInput(GetActorForwardVector(),  Value); }
void ALedgerCharacter::MoveBackward(float Value) { AddMovementInput(GetActorForwardVector(), -Value); }
void ALedgerCharacter::MoveRight(float Value)    { AddMovementInput(GetActorRightVector(),    Value); }
void ALedgerCharacter::MoveLeft(float Value)     { AddMovementInput(GetActorRightVector(),   -Value); }
void ALedgerCharacter::LookYaw(float Value)      { AddControllerYawInput(Value); }
void ALedgerCharacter::LookPitch(float Value)    { AddControllerPitchInput(-Value); }
