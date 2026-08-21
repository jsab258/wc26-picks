// CONTACT BLOB UNDER A BODY — the cheapest grounding there is (M17.10).
//
// The real sun shadow of a walking figure at street distance is a few dozen
// pixels the 5x5 PCF blur mostly eats, and light probes are structurally
// unavailable in a project generated fresh by CI (probe groups are bake-time
// input). A multiplied radial blob under the root is the PS3-era answer and
// it is the one GTA-generation crowds actually shipped: every body sits DOWN
// on the pavement instead of floating a millimetre above it.
//
// MULTIPLICATIVE (DstColor Zero), so it darkens whatever is under it —
// sunlit slab, wet tarmac, painted line — and needs no lighting code at all.
// The known, accepted era artefact: where a building's cast shadow already
// falls, the blob double-darkens slightly. Every reference frame carries the
// same artefact.
//
// FOG FADES IT TO WHITE, not to fog colour: a multiplier's identity is 1,
// and fading toward anything else stamps dark rectangles through the haze at
// fifty metres — the classic multiplicative-decal giveaway.
Shader "Hidden/LedgerBlob"
{
    Properties
    {
        _MainTex ("Falloff", 2D) = "white" {}
        _Strength ("Strength", Range(0, 1)) = 0.42
    }
    SubShader
    {
        Tags { "Queue" = "AlphaTest+1" "RenderType" = "Transparent" }
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
                float a = tex2D(_MainTex, i.uv).a * _Strength;
                fixed4 col = fixed4(1 - a, 1 - a, 1 - a, 1);
                UNITY_APPLY_FOG_COLOR(i.fogCoord, col, fixed4(1, 1, 1, 1));
                return col;
            }
            ENDCG
        }
    }
    Fallback Off
}
