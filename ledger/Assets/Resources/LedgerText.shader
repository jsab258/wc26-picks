// WORLD TEXT THAT IS IN THE WORLD, instead of painted on the lens.
//
// FOUND BY LOOKING AT A SCREENSHOT, on the first night the pipeline could
// commit one. Two faults in the same frame, one cause:
//
//   * A character's name floated over the SKYLINE. "Lucille Salas" sat across
//     the rooftops at noon; "Victor" lay over a dark building at night. The
//     walkers those names belong to were behind that geometry.
//   * Every street sign read as garbled overlapping glyphs. `StreetFurniture`
//     makes a plate double-sided by placing a second TextMesh rotated 180
//     degrees, five centimetres the other side of a six-centimetre board — so
//     the far copy should be hidden by the board and instead drew straight
//     through it, mirrored, on top of the near one.
//
// Unity's built-in `GUI/Text Shader` is `Cull Off, ZWrite Off, ZTest Always`.
// Always means the glyph is drawn whatever is in front of it, which is right
// for a HUD and wrong for a label standing in a street. Both faults above are
// that one line, and the screenshots are the evidence rather than my memory of
// what the built-in shader does.
//
// IN `Resources` BECAUSE THAT IS THE ONLY PLACE THAT SURVIVES A BUILD. The
// noise ring spent three CI runs learning this: `Shader.Find("Sprites/Default")`
// returns null in the player because the shader is not included, and assigning
// null measures pixel-for-pixel the same as assigning nothing. Everything in
// `Assets/Resources` is in the player by definition.
//
// WHAT IT HAS TO DO:
//   - ZTest LEqual, so a name behind a wall is behind the wall. The entire
//     point.
//   - Cull Back, so the mirrored reverse of a glyph is never drawn. That alone
//     fixes the double-sided sign without removing the second plate.
//   - Alpha blended against the font atlas, which stores the glyph in its
//     alpha channel — a font texture sampled for RGB is a white rectangle.
//   - Vertex colour, because `TextMesh.color` arrives per-vertex and the NPC
//     labels fade in on approach through its alpha. A shader that ignores it
//     turns that fade into a pop, and every label would render at full white.
//   - ZWrite Off, because glyph quads overlap and a depth-writing letter
//     punches a hole in the letter beside it.
Shader "Hidden/LedgerText"
{
    Properties
    {
        _MainTex ("Font Atlas", 2D) = "white" {}
        _Color ("Text Color", Color) = (1,1,1,1)
    }

    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" }
        Lighting Off
        Cull Back
        ZWrite Off
        ZTest LEqual
        Fog { Mode Off }
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv     : TEXCOORD0;
                fixed4 color  : COLOR;
            };

            struct v2f
            {
                float4 pos   : SV_POSITION;
                float2 uv    : TEXCOORD0;
                fixed4 color : COLOR;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.color = v.color * _Color;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // THE GLYPH IS IN THE ALPHA CHANNEL of the font atlas. Sampling
                // RGB gives a solid block, which is how a "working" text shader
                // renders every label as a white rectangle.
                fixed4 c = i.color;
                c.a *= tex2D(_MainTex, i.uv).a;
                return c;
            }
            ENDCG
        }
    }

    Fallback off
}
