// THE NOISE RING'S OWN SHADER, and it exists because of a measurement.
//
// Three separate attempts to draw this circle with a built-in shader failed in
// a built player, and CI told me so one at a time at half an hour a go:
//
//   * a LineRenderer created at runtime has NO material in this build.
//     `sharedMaterial` comes back null, so the assumption that the component
//     "already owns Unity's built-in line material" was simply wrong, and the
//     shipping path rejected four perfectly good rings for it.
//   * `Sprites/Default` is not in the build at all. `Shader.Find` returns null,
//     which is why assigning it measured pixel-for-pixel the same as assigning
//     nothing. My very first guess — "the sprite shader was stripped" — turns
//     out to have been true of the shader and irrelevant to the bug.
//   * `Legacy Shaders/Particles/Alpha Blended` IS in the build and drew
//     nothing measurable.
//
// The three shaders this project relies on — the grade, the shafts, the
// occlusion pass — all live in `Assets/Resources`, and everything in there is
// included in the player by definition. That is the whole reason they work
// where `Shader.Find("Sprites/Default")` does not. So the ring gets one too,
// and stops depending on what a given Unity version happens to ship.
//
// WHAT IT HAS TO DO, and each line below is one of those requirements:
//   - UNLIT. A lit shader on a circle lying in a 3am street is a black circle.
//     The ring is a diagram drawn over the world, not a thing in it.
//   - VERTEX COLOUR, because the fade is per-vertex alpha from the
//     LineRenderer's own gradient. A shader ignoring vertex colour turns the
//     fade into a pop.
//   - ALPHA BLENDED, so it lies over the road rather than punching a hole.
//   - ZWrite off and ZTest always: it is four centimetres off the ground and
//     the camera is often nearly level with it, so depth-testing it against a
//     wet road at a grazing angle is a fight it loses for no benefit. Drawing
//     over geometry is correct for a legibility overlay — it is the same call
//     the light shafts already make.
Shader "Hidden/LedgerRing"
{
    Properties { _Tint ("Tint", Color) = (1,1,1,1) }

    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Cull Off
        ZWrite Off
        ZTest Always
        Blend SrcAlpha OneMinusSrcAlpha
        Lighting Off
        Fog { Mode Off }

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            fixed4 _Tint;

            struct appdata
            {
                float4 vertex : POSITION;
                fixed4 color  : COLOR;
            };
            struct v2f
            {
                float4 pos   : SV_POSITION;
                fixed4 color : COLOR;
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.color = v.color * _Tint;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target { return i.color; }
            ENDCG
        }
    }

    // No fallback on purpose. If this cannot compile there is nothing sensible
    // to fall back TO — that is the whole finding above — and a silent fallback
    // to something invisible is how this cost four builds.
}
