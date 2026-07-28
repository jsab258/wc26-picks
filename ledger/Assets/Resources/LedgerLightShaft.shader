// VOLUMETRIC LIGHT SHAFTS (the-gap.md §3a).
//
// A cone of participating medium under every lamp. This is the single
// effect that most separates "a scene with lights in it" from "a
// photograph of a street at night", and it costs no art.
//
// Cone GEOMETRY rather than a screen-space raymarch, deliberately:
//   - it is correct in 3D, so it occludes and parallaxes properly and you
//     can walk through it;
//   - it needs no depth texture, so it cannot fail into a black screen on
//     a machine whose depth mode is not what we assumed;
//   - it costs one small additive draw per lamp instead of a fullscreen
//     march per frame.
//
// The three things that stop a cone looking like a cone-shaped OBJECT:
//
//   1. RIM FADE. Fade out where the surface faces the camera edge-on. This
//      is the whole trick — without it you see a hard silhouette and the
//      illusion dies instantly.
//   2. FORWARD SCATTERING. Fog scatters forward, so the shaft is far
//      brighter looking toward the lamp than away from it (Henyey-
//      Greenstein, matching Core/LightModel.Phase).
//   3. NEAR FADE. Fade as the camera gets close, or walking into a lamp
//      pool flashes the whole screen as the near plane clips the cone.
Shader "Hidden/LedgerLightShaft"
{
    Properties
    {
        _Color ("Colour", Color) = (1, 0.82, 0.55, 1)
        _Intensity ("Intensity", Float) = 1
        _Anisotropy ("Anisotropy", Range(0, 0.95)) = 0.62
    }
    SubShader
    {
        Tags { "Queue" = "Transparent+100" "RenderType" = "Transparent"
               "IgnoreProjector" = "True" }

        // Additive: light ADDS to what is behind it, it does not replace it.
        // Alpha blending here would darken the world through the shaft.
        Blend One One
        ZWrite Off
        // Cull Off so it survives being stood inside — the player walks
        // through these constantly.
        Cull Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            fixed4 _Color;
            float _Intensity, _Anisotropy;

            struct v2f
            {
                float4 pos    : SV_POSITION;
                float3 normal : TEXCOORD0;
                float3 view   : TEXCOORD1;   // fragment -> camera, world
                float3 toLamp : TEXCOORD2;   // fragment -> apex, world
                float  along  : TEXCOORD3;   // 0 at the bulb, 1 at the lip
                float  dist   : TEXCOORD4;   // camera distance, for the near fade
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                float3 world = mul(unity_ObjectToWorld, v.vertex).xyz;
                float3 apex  = mul(unity_ObjectToWorld, float4(0, 0, 0, 1)).xyz;
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.view   = _WorldSpaceCameraPos - world;
                o.toLamp = apex - world;
                // The cone mesh is built with y from 0 at the apex to -1 at
                // the lip, so the texcoord carries the position along it.
                o.along  = saturate(v.texcoord.y);
                o.dist   = length(o.view);
                return o;
            }

            // Henyey-Greenstein, the same function as Core/LightModel.Phase.
            // Normalised against its own isotropic value so _Intensity means
            // the same thing whatever the anisotropy is set to.
            float phase(float cosTheta, float g)
            {
                float gg = g * g;
                float d = 1.0 + gg - 2.0 * g * cosTheta;
                return (1.0 - gg) / pow(max(d, 1e-4), 1.5);
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float3 V = normalize(i.view);
                float3 N = normalize(i.normal);
                float3 L = normalize(i.toLamp);

                // 1. RIM FADE — the trick that hides the silhouette. Surface
                // facing the camera contributes; surface seen edge-on does
                // not. Squared so the falloff is soft rather than linear.
                float rim = saturate(dot(N, V));
                rim *= rim;

                // 2. FORWARD SCATTERING. Looking INTO the lamp is bright;
                // looking away from it is nearly nothing. This asymmetry is
                // why the result reads as light rather than as geometry.
                float scatter = phase(saturate(dot(-V, -L)), _Anisotropy);

                // Along the cone: brightest at the bulb, gone by the lip.
                float along = 1.0 - i.along;
                along *= along;

                // 3. NEAR FADE. Without this, walking under a lamp clips the
                // cone against the near plane and flashes the whole frame.
                float near = smoothstep(0.35, 2.2, i.dist);

                // And a far fade, so distant lamps do not stack into a haze
                // that washes out the far end of the street.
                float far = 1.0 - smoothstep(45.0, 95.0, i.dist);

                float a = rim * scatter * along * near * far * _Intensity;
                return fixed4(_Color.rgb * a, 1.0);
            }
            ENDCG
        }
    }
    Fallback Off
}
