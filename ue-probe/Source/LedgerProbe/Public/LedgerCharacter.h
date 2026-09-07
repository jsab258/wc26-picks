// THE PLAYER'S BODY IN THE STREET.
//
// Queue 138 item 1: "a character I can control in the textured street,
// with a camera." Two verbs only, walk and look, so this class carries
// two axes of movement and two axes of mouse look and nothing else: no
// jump, no crouch, no interact. Built from the engine's own Character,
// CharacterMovementComponent, SpringArmComponent and CameraComponent
// rather than anything bespoke, per the brief.
//
// NO CONTENT ASSET ANYWHERE HERE. This project ships no hand-made
// uasset, and there is no Mixamo body in ue-probe yet, so this capsule
// carries no visible mesh. The camera still shows the textured street
// around an invisible body, which is the same "spawn a shape from code,
// not a hand-placed asset" discipline the street itself is built on.
//
// INPUT IS BOUND DIRECTLY TO KEYS, NOT THROUGH A NAMED MAPPING. Checked
// rather than assumed: ue-probe/Config carries no DefaultInput.ini (the
// file does not exist), so there is no legacy axis mapping already in
// this project to join, and there is no Input Mapping Context asset and
// no Enhanced Input module dependency in LedgerProbe.Build.cs either.
// Adding Enhanced Input to reach the same two axes would be a brand new
// module dependency, a brand new pair of runtime-constructed UObjects
// (UInputAction, UInputMappingContext), and the first user of any of the
// three in this codebase, all unverifiable until the next Windows build.
// UInputComponent::BindAxisKey and BindKey bind straight to a hardware
// FKey, need no Project Settings entry and no content asset, have not
// changed shape since UE4, and Epic's own documentation states Enhanced
// Input is designed to run ALONGSIDE this mechanism rather than replace
// it, so this works whichever input component class the project's
// default resolves to.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "LedgerCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UInputComponent;

UCLASS()
class ALedgerCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ALedgerCharacter();

protected:
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "Ledger")
	USpringArmComponent* CameraBoom;

	UPROPERTY(VisibleAnywhere, Category = "Ledger")
	UCameraComponent* FollowCamera;

	// EACH KEY OWNS ONE SIGNED CONTRIBUTION rather than one shared axis
	// composed from two raw keys by hand: W and S each call AddMovementInput
	// with an opposite sign, and the same shape covers A and D.
	void MoveForward(float Value);
	void MoveBackward(float Value);
	void MoveRight(float Value);
	void MoveLeft(float Value);
	void LookYaw(float Value);
	void LookPitch(float Value);
};
