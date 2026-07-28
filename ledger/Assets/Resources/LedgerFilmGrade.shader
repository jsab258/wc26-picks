// Grain, vignette and bloom in one shader (art direction §4, "Post: film
// grain, vignette, slight bloom on light sources").
//
// Hand-written rather than the Post Processing package for the same reason
// every asset in this project is synthesised: no extra package, no version
// to pin, no import step, and it works in the built player today.
//
// Five passes. 0 composites, 1 extracts the bright pixels, 2 blurs,
// 3 computes ambient occlusion, 4 blurs it without crossing an edge.
Shader "Hidden/LedgerFilmGrade"
{
    Properties
    {
        _MainTex ("Source", 2D) = "white" {}
    }
    SubShader
    {
        Cull Off ZWrite Off ZTest Always

        CGINCLUDE
        #include "UnityCG.cginc"
        sampler2D _MainTex;
        float4 _MainTex_TexelSize;
        sampler2D _BloomTex;
        sampler2D _AoTex;
        sampler2D _CameraDepthNormalsTexture;
        float _Threshold, _Bloom, _Grain, _Vignette, _Seed, _Exposure;
        float _AoStrength, _AoRadius, _AoRelief, _AoFloor;
        float4 _Dir;
        float4 _AoTexelSize;
        float4x4 _AoProj;

        // ACES filmic tonemap (Narkowicz fit) — the same curve as
        // Core/LightModel.Aces, which is where its properties are tested.
        //
        // THIS IS THE DIFFERENCE BETWEEN A PHOTOGRAPH AND A CLAMP. A linear
        // clamp takes everything over 1.0 to white, which is precisely how a
        // red neon sign becomes a white rectangle — the defect the palette
        // pass fixed at the source and which the post stack was still
        // capable of reintroducing one level down. A filmic curve rolls the
        // highlights off instead: they compress, the hue survives, and the
        // eye reads it as exposure rather than as damage.
        float3 aces(float3 x)
        {
            const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
            return saturate((x * (a * x + b)) / (x * (c * x + d) + e));
        }

        struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };
        v2f vert(appdata_img v)
        {
            v2f o;
            o.pos = UnityObjectToClipPos(v.vertex);
            o.uv = v.texcoord;
            return o;
        }

        // Cheap hash. Good enough for grain, which wants to look random
        // rather than be random.
        float hash(float2 p)
        {
            return frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453);
        }
        ENDCG

        // ---- pass 0: composite ----
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);

                // BLOOM. Added, not lerped: a lamp does not replace what is
                // behind it, it spills over it. This is also what recovers
                // the colour that low-dynamic-range clipping takes off a
                // neon sign, by spreading hue into the pixels AROUND the
                // highlight rather than only inside it.
                fixed3 bloom = tex2D(_BloomTex, i.uv).rgb;
                col.rgb += bloom * _Bloom;

                // AMBIENT OCCLUSION, and it goes here — scene-referred,
                // BEFORE the tonemap. Darkening after the curve subtracts
                // display values and grinds contact shadows to mud; before
                // it, the curve rolls them off the way it rolls off
                // everything else, and a corner reads as less light rather
                // than as a stain.
                //
                // It also goes on before bloom would have been a mistake:
                // bloom is light spilling from elsewhere and does not care
                // whether the surface it lands on is in a corner. So bloom
                // first, then occlude what the surface itself receives.
                float aoRaw = tex2D(_AoTex, i.uv).r;
                float aoLum = dot(col.rgb, float3(0.299, 0.587, 0.114));
                // Mirrors Core/LightModel.AoMultiplier, which is where these
                // numbers are tested.
                float ao = 1.0 - saturate(aoRaw) * _AoStrength
                                * (1.0 - _AoRelief * saturate(aoLum));
                col.rgb *= max(ao, _AoFloor);

                // EXPOSURE then TONEMAP, in that order and before anything
                // else. Exposure is a scene-referred operation and vignette
                // and grain are display-referred ones; doing them the other
                // way round grades the vignette instead of the image.
                col.rgb = aces(col.rgb * _Exposure);

                // VIGNETTE. Pulls the eye to the middle and makes the frame
                // feel photographed. Squared so it stays off the centre
                // entirely rather than dimming the whole image.
                float2 d = i.uv - 0.5;
                float v = saturate(1.0 - dot(d, d) * _Vignette * 4.0);
                col.rgb *= v * v;

                // GRAIN, and the reason it earns its place: it hides banding
                // in a dark blue-teal sky, hides the flatness of untextured
                // geometry, and unifies disparate assets under one film
                // stock. Signed so it does not only ever brighten, and
                // scaled by (1 - luminance) so it lands in the shadows where
                // film grain actually lives instead of speckling the lamps.
                float g = hash(i.uv * _MainTex_TexelSize.zw + _Seed) - 0.5;
                float lum = dot(col.rgb, float3(0.299, 0.587, 0.114));
                col.rgb += g * _Grain * (1.0 - lum * 0.7);

                return col;
            }
            ENDCG
        }

        // ---- pass 1: bright pass ----
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);
                float lum = dot(col.rgb, float3(0.299, 0.587, 0.114));
                // Soft knee rather than a hard cut, or every bloom edge
                // becomes a visible contour where the threshold sits.
                float k = saturate((lum - _Threshold) / max(0.001, 1.0 - _Threshold));
                return fixed4(col.rgb * k * k, 1.0);
            }
            ENDCG
        }

        // ---- pass 2: separable blur ----
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            fixed4 frag(v2f i) : SV_Target
            {
                float2 d = _Dir.xy;
                fixed3 sum = tex2D(_MainTex, i.uv).rgb * 0.227;
                sum += tex2D(_MainTex, i.uv + d * 1.38).rgb * 0.316;
                sum += tex2D(_MainTex, i.uv - d * 1.38).rgb * 0.316;
                sum += tex2D(_MainTex, i.uv + d * 3.23).rgb * 0.070;
                sum += tex2D(_MainTex, i.uv - d * 3.23).rgb * 0.070;
                return fixed4(sum, 1.0);
            }
            ENDCG
        }

        // ---- pass 3: ambient occlusion ----
        //
        // Untextured geometry reads flat because nothing sits IN anything —
        // the corner where a bin meets a wall is lit exactly as brightly as
        // the open pavement beside it, so the bin floats. Contact darkening
        // is how the eye places an object on a surface, and it is the last
        // large difference between this render and a photographed one that
        // costs no assets at all.
        //
        // Horizon-style sampling off DepthNormals: take points in a disc
        // around the pixel, and count the ones that sit in FRONT of the
        // surface's own plane. That is what being occluded means.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0

            // Twelve taps on a spiral. A spiral rather than a fixed kernel
            // because a regular grid produces visible banding on curved
            // surfaces, and twelve because the blur that follows can hide
            // the noise of a low count but cannot invent structure a high
            // one would have found.
            static const float2 kTaps[12] = {
                float2( 0.000,  0.300), float2( 0.335,  0.335),
                float2( 0.520,  0.000), float2( 0.494, -0.494),
                float2( 0.000, -0.735), float2(-0.593, -0.593),
                float2(-0.850,  0.000), float2(-0.671,  0.671),
                float2( 0.000,  0.949), float2( 0.742,  0.742),
                float2( 1.050,  0.000), float2( 0.795, -0.795),
            };

            // ONE HANDEDNESS, and this is the bug that would have shipped.
            //
            // `DecodeDepthNormal` returns a view-space normal in Unity's
            // frame, where the camera looks down -Z, so a surface facing the
            // camera has a normal near (0,0,-1). The position reconstructed
            // below puts depth on +Z, because depth grows away from the eye.
            // Those are opposite handednesses, and `dot(n, sample - p)` with
            // the two mixed comes out INVERTED: occlusion appears on convex
            // edges instead of in concave corners, which is haloing — a
            // bright rim on every object rather than a dark seam under it.
            //
            // It would have looked like a broken effect rather than a sign
            // error, and the A/B gate that proves AO reaches pixels would
            // have passed the whole time: the frame is darker either way.
            float3 ViewPos(float2 uv, out float3 normal)
            {
                float depth;
                DecodeDepthNormal(tex2D(_CameraDepthNormalsTexture, uv), depth, normal);
                normal.z = -normal.z;
                float eye = depth * _ProjectionParams.z;
                // Reconstruct the view ray from the clip-space position.
                float2 ndc = uv * 2.0 - 1.0;
                float3 ray = float3(ndc.x / _AoProj[0][0], ndc.y / _AoProj[1][1], 1.0);
                return ray * eye;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float3 n;
                float3 p = ViewPos(i.uv, n);
                // Nothing was drawn here. The skybox must not be occluded —
                // AO on the sky is the other unmistakable tell.
                if (p.z >= _ProjectionParams.z * 0.99) return fixed4(0, 0, 0, 1);

                // A per-pixel rotation, so the twelve taps do not land on the
                // same twelve angles everywhere and print the kernel across
                // the frame as a visible pattern.
                float a = hash(i.uv * _AoTexelSize.zw) * 6.2831853;
                float2 rc = float2(cos(a), sin(a));

                // The disc shrinks with distance, so the radius stays roughly
                // constant IN METRES rather than in pixels — otherwise
                // everything far away is uniformly grey.
                float scale = _AoRadius / max(0.1, p.z);

                float occ = 0;
                [unroll] for (int t = 0; t < 12; t++)
                {
                    float2 o = float2(kTaps[t].x * rc.x - kTaps[t].y * rc.y,
                                      kTaps[t].x * rc.y + kTaps[t].y * rc.x);
                    float2 uv = i.uv + o * scale;
                    float3 sn;
                    float3 sp = ViewPos(uv, sn);
                    float3 d = sp - p;
                    float len = length(d);
                    if (len < 1e-4) continue;

                    // How far the sample sits ABOVE this surface's plane.
                    // Negative means behind it, which is not occlusion.
                    float above = dot(n, d / len);
                    // The range check from Core/LightModel.AoRangeCheck: a
                    // sample metres in front belongs to another object, and
                    // counting it draws the dark halo round every silhouette
                    // that gives cheap occlusion away.
                    float range = saturate(1.0 - max(0, len - _AoRadius) / _AoRadius);
                    // A small bias, or a flat surface occludes itself into a
                    // grey haze from depth-buffer precision alone.
                    occ += max(0, above - 0.035) * range;
                }
                return fixed4(saturate(occ / 12.0 * 2.4), 0, 0, 1);
            }
            ENDCG
        }

        // ---- pass 4: edge-aware blur for the occlusion ----
        //
        // Twelve taps is noisy and has to be blurred, but an ordinary blur
        // drags occlusion across silhouettes and puts a shadow of the
        // foreground onto the background. So each tap is weighted by how
        // close its DEPTH is to the centre's: blur along a surface, never
        // across a discontinuity.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            fixed4 frag(v2f i) : SV_Target
            {
                float2 d = _Dir.xy;
                float3 n;
                float dc;
                DecodeDepthNormal(tex2D(_CameraDepthNormalsTexture, i.uv), dc, n);

                float sum = tex2D(_MainTex, i.uv).r * 0.227;
                float wsum = 0.227;
                float w[4] = { 0.316, 0.316, 0.070, 0.070 };
                float2 offs[4] = { d * 1.38, -d * 1.38, d * 3.23, -d * 3.23 };
                [unroll] for (int k = 0; k < 4; k++)
                {
                    float2 uv = i.uv + offs[k];
                    float ds;
                    float3 ns;
                    DecodeDepthNormal(tex2D(_CameraDepthNormalsTexture, uv), ds, ns);
                    // 2cm of depth at a metre. Tight enough to stop at an
                    // edge, loose enough not to stop on a sloped floor.
                    float edge = saturate(1.0 - abs(ds - dc) * _ProjectionParams.z * 8.0);
                    float ww = w[k] * edge;
                    sum += tex2D(_MainTex, uv).r * ww;
                    wsum += ww;
                }
                return fixed4(sum / max(1e-4, wsum), 0, 0, 1);
            }
            ENDCG
        }
    }
    Fallback Off
}
