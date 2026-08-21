// STREET GRIME — the M17.10 V2 surface-history layer.
//
// MULTIPLICATIVE, like the contact blob and for the same reasons: a stain
// needs no lighting code, because it darkens whatever light is already on
// the surface under it — a sunlit slab keeps its sun, a shadowed one its
// shade, and the AO pass reads the result like any other pixel. This is the
// era-correct GTA grime: their streets are quads of exactly this kind.
//
// The texture convention: RGB is the stain's own tint (white = untouched),
// A is its shape. `_Strength` scales the whole layer so one number can
// tune a district's filth.
//
// FOG FADES TO WHITE — the multiplier's identity — never to fog colour,
// or every stain becomes a dark stamp floating in the haze at distance.
Shader "Hidden/LedgerDecal"
{
    Properties
    {
        _MainTex ("Decal", 2D) = "white" {}
        _Strength ("Strength", Range(0, 1)) = 0.85
    }
    SubShader
    {
        Tags { "Queue" = "AlphaTest+2" "RenderType" = "Transparent" }
        Blend DstColor Zero
        ZWrite Off
        Offset -1, -1

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float _Strength;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_FOG_COORDS(1)
            };

            v2f vert(appdata_img v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.texcoord;
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 t = tex2D(_MainTex, i.uv);
                // Blend from identity (white) toward the stain's tint by its
                // shape and the layer strength.
                fixed3 mul3 = lerp(fixed3(1, 1, 1), t.rgb, t.a * _Strength);
                fixed4 col = fixed4(mul3, 1);
                UNITY_APPLY_FOG_COLOR(i.fogCoord, col, fixed4(1, 1, 1, 1));
                return col;
            }
            ENDCG
        }
    }
    Fallback Off
}
