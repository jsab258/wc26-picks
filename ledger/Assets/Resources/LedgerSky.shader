// THE SKY — a three-stop gradient, driven every frame from Core/LightModel.
//
// There was no skybox anywhere in this project until 15 Aug. The camera
// cleared to the fog colour, so the sky was a flat card the exact colour of
// maximum fog — and `LightModel.SkyColour/HorizonColour/GroundColour`, a
// correct day/night/rain gradient computed every frame, was wired only into
// the ambient trilight. The one place the art direction leans hardest (a low
// wet British sky over a port town) was showing the fallback.
//
// WHY THE HORIZON STOP IS THE FOG COLOUR, not `HorizonColour`: the skybox
// draws behind everything and Unity's fog does not apply to it. Geometry at
// the far end of a street dissolves toward `RenderSettings.fogColor`, so if
// the sky's horizon band were any OTHER colour, every street would end in a
// visible seam between fogged brick and un-fogged sky. Feeding the fog colour
// into `_HorizonColor` makes the seam impossible by construction — which is
// the same job the old SolidColor clear did, kept, with an actual sky above.
//
// In `Assets/Resources` because that is the one place a runtime-found shader
// is guaranteed into the player — measured the hard way, see LedgerRing.
//
// The curves: >1 keeps the horizon band BROAD (low marine haze climbing into
// cloud), which is the look; <1 would snap to the zenith colour a few degrees
// up. Properties rather than constants so a still can be answered by a
// material tweak in C# without touching this file.
Shader "Hidden/LedgerSky"
{
    Properties
    {
        _SkyColor     ("Sky (zenith)",   Color) = (0.55, 0.62, 0.72, 1)
        _HorizonColor ("Horizon (fog)",  Color) = (0.67, 0.64, 0.63, 1)
        _GroundColor  ("Ground (below)", Color) = (0.30, 0.28, 0.26, 1)
        _SkyCurve     ("Sky curve",      Float) = 1.7
        _GroundCurve  ("Ground curve",   Float) = 1.2
    }

    SubShader
    {
        Tags { "Queue" = "Background" "RenderType" = "Background" "PreviewType" = "Skybox" }
        Cull Off
        ZWrite Off
        Fog { Mode Off }

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            fixed4 _SkyColor;
            fixed4 _HorizonColor;
            fixed4 _GroundColor;
            float  _SkyCurve;
            float  _GroundCurve;

            struct appdata { float4 vertex : POSITION; };
            struct v2f
            {
                float4 pos : SV_POSITION;
                // The skybox mesh is a unit cube around the camera, so the
                // OBJECT-SPACE vertex position is the view direction.
                float3 dir : TEXCOORD0;
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.dir = v.vertex.xyz;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float h = normalize(i.dir).y;
                float up = pow(saturate(h), _SkyCurve);
                float dn = pow(saturate(-h), _GroundCurve);
                fixed4 c = lerp(_HorizonColor, _SkyColor, up);
                c = lerp(c, _GroundColor, dn);
                c.a = 1;
                return c;
            }
            ENDCG
        }
    }

    // No fallback, same reasoning as the ring: everything sensible to fall
    // back to is the bug this shader fixes.
}
