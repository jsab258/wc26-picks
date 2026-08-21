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
        // CLOUD STRUCTURE (M17.10 V6, pulled early because an empty gradient
        // dome is the loudest remaining sky tell). Value-noise FBM on a
        // virtual plane; the colour and coverage are driven per frame from
        // SceneLighting so the clouds keep the dome's own palette.
        _CloudColor    ("Cloud colour",  Color) = (0.50, 0.56, 0.64, 1)
        _CloudCoverage ("Cloud coverage", Range(0, 1)) = 0.65
        _CloudScale    ("Cloud scale",   Float) = 1.6
        _CloudWind     ("Cloud wind xy", Vector) = (0.006, 0.0035, 0, 0)
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
            fixed4 _CloudColor;
            float  _CloudCoverage;
            float  _CloudScale;
            float4 _CloudWind;

            // Value noise + 3-octave FBM with one domain warp. Hash-based
            // because CG has no Perlin; good enough for cloud MASSES — the
            // grade and the fog eat the small-scale detail anyway.
            float vhash(float2 p)
            {
                return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }
            float vnoise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                float a = vhash(i);
                float b = vhash(i + float2(1, 0));
                float c = vhash(i + float2(0, 1));
                float d = vhash(i + float2(1, 1));
                return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
            }
            float fbm(float2 p)
            {
                float n = 0.0, amp = 0.55;
                for (int o = 0; o < 3; o++)
                {
                    n += vnoise(p) * amp;
                    p = p * 2.13 + 17.7;
                    amp *= 0.5;
                }
                return n;
            }

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
                float3 nd = normalize(i.dir);
                float h = nd.y;
                float up = pow(saturate(h), _SkyCurve);
                float dn = pow(saturate(-h), _GroundCurve);
                fixed4 c = lerp(_HorizonColor, _SkyColor, up);
                c = lerp(c, _GroundColor, dn);

                // CLOUDS on a virtual plane overhead. The projection divides
                // by the view's up-component, so masses compress toward the
                // horizon the way a real cloud deck does. One domain warp
                // breaks the value-noise blockiness.
                //
                // FADED OUT AT THE HORIZON BY `up`, which keeps the standing
                // guarantee this file exists for: the horizon band stays
                // EXACTLY the fog colour, so the fogged-street-to-sky seam
                // remains impossible by construction. Clouds live in the
                // upper sky; the marine haze owns the bottom.
                if (h > 0.02)
                {
                    float2 uv = nd.xz / max(h, 0.08) * _CloudScale
                              + _CloudWind.xy * _Time.y;
                    float2 warp = float2(fbm(uv * 0.7 + 31.4), fbm(uv * 0.7 - 12.9));
                    float n = fbm(uv + (warp - 0.5) * 0.9);
                    // Coverage remaps the noise band into cloud opacity:
                    // higher coverage pulls more of the mid-band into cloud.
                    float cl = smoothstep(1.0 - _CloudCoverage - 0.25,
                                          1.0 - _CloudCoverage + 0.25, n);
                    c.rgb = lerp(c.rgb, _CloudColor.rgb, cl * up * 0.85);
                }
                c.a = 1;
                return c;
            }
            ENDCG
        }
    }

    // No fallback, same reasoning as the ring: everything sensible to fall
    // back to is the bug this shader fixes.
}
