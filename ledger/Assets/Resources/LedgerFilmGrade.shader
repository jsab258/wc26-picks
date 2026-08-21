// Grain, vignette and bloom in one shader (art direction §4, "Post: film
// grain, vignette, slight bloom on light sources").
//
// Hand-written rather than the Post Processing package for the same reason
// every asset in this project is synthesised: no extra package, no version
// to pin, no import step, and it works in the built player today.
//
// Three passes. 0 composites, 1 extracts the bright pixels, 2 blurs.
//
// Ambient occlusion lives in its OWN shader, deliberately. A compile
// failure in any pass makes `Shader.isSupported` false for the whole
// shader, and FilmGrade fails closed on that — so a broken AO pass would
// have taken grain, vignette, bloom and the tonemap down with it. This
// file's own header says an art effect that can break the picture must
// never be able to; a newer, riskier effect sharing its compilation unit
// is exactly that, one level down.
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
        // The AO RESULT is read here; the AO itself is computed in
        // LedgerAo.shader, which owns the depth-normals sampler and the
        // projection matrix. This file only multiplies by what comes back.
        sampler2D _AoTex;
        float _Threshold, _Bloom, _Grain, _Vignette, _Seed, _Exposure;
        // EXPOSED COOLS, HIDDEN WARMS. Two multipliers rather than a colour,
        // because green is deliberately untouched: a tint that moves all three
        // channels is a colour grade, and this has to stay under the threshold
        // where anybody consciously notices while staying over the one where
        // they feel it. LightModel.TemperatureSwing is 0.008 — under one
        // percent — and computed in Core so a test can hold it.
        float _TempR, _TempB;
        float _AoStrength, _AoRelief, _AoFloor;
        float4 _Dir;

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

                // AMBIENT OCCLUSION FIRST, THEN BLOOM — the old order was
                // backwards BY ITS OWN ARGUMENT. The comment that stood here
                // said "bloom is light spilling from elsewhere and does not
                // care whether the surface it lands on is in a corner", and
                // then the code added bloom INTO col and multiplied the sum
                // by the occlusion — occluding the bloom, the exact thing
                // the sentence says must not happen. At night that ate the
                // lamp glow in every corner the AO found. Occlude what the
                // surface receives; spill the lens light over the result.
                //
                // Still scene-referred, BEFORE the tonemap: darkening after
                // the curve subtracts display values and grinds contact
                // shadows to mud; before it, the curve rolls them off like
                // everything else and a corner reads as less light rather
                // than as a stain.
                float aoRaw = tex2D(_AoTex, i.uv).r;
                float aoLum = dot(col.rgb, float3(0.299, 0.587, 0.114));
                // Mirrors Core/LightModel.AoMultiplier, which is where these
                // numbers are tested.
                float ao = 1.0 - saturate(aoRaw) * _AoStrength
                                * (1.0 - _AoRelief * saturate(aoLum));
                col.rgb *= max(ao, _AoFloor);

                // BLOOM. Added, not lerped: a lamp does not replace what is
                // behind it, it spills over it. This is also what recovers
                // the colour that low-dynamic-range clipping takes off a
                // neon sign, by spreading hue into the pixels AROUND the
                // highlight rather than only inside it.
                fixed3 bloom = tex2D(_BloomTex, i.uv).rgb;
                col.rgb += bloom * _Bloom;

                // EXPOSURE then TONEMAP, in that order and before anything
                // else. Exposure is a scene-referred operation and vignette
                // and grain are display-referred ones; doing them the other
                // way round grades the vignette instead of the image.
                // TEMPERATURE BEFORE THE TONEMAP, for the same reason
                // exposure is: it is a scene-referred operation. Applied
                // after the tonemap it would tint the shoulder rather than
                // the light, and the effect would vanish in the highlights —
                // which are exactly the lit areas it exists to cool.
                col.rgb *= float3(_TempR, 1.0, _TempB);
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

    }
    Fallback Off
}
