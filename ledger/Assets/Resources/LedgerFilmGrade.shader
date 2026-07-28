// Grain, vignette and bloom in one shader (art direction §4, "Post: film
// grain, vignette, slight bloom on light sources").
//
// Hand-written rather than the Post Processing package for the same reason
// every asset in this project is synthesised: no extra package, no version
// to pin, no import step, and it works in the built player today.
//
// Three passes. 0 composites, 1 extracts the bright pixels, 2 blurs.
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
        float _Threshold, _Bloom, _Grain, _Vignette, _Seed;
        float4 _Dir;

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
