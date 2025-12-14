#include <cstdio>
#include <cstring>
#include "../../resources/rmkit/src/vendor/stb/stb_truetype.h"

// Simple font test - no rm2fb, no UI framework
// Just validates font can be loaded and queried

#ifdef FONT_EMBED_H
#include FONT_EMBED_H
#else
// Use system font fallback
#define FONT_EMBED_NAME NULL
#define FONT_EMBED_LEN 0
#endif

int main() {
    printf("========================================\n");
    printf("Font Validation Test\n");
    printf("========================================\n\n");

    unsigned char font_buffer[24<<20];
    stbtt_fontinfo font;
    bool success = false;

    // Try embedded font first
    if (FONT_EMBED_NAME != NULL && FONT_EMBED_LEN > 0) {
        printf("Testing embedded font...\n");
        memcpy(font_buffer, FONT_EMBED_NAME, FONT_EMBED_LEN);
        font_buffer[FONT_EMBED_LEN] = 0;

        int result = stbtt_InitFont(&font, font_buffer, 0);
        if (result) {
            printf("✓ Embedded font loaded successfully\n");
            success = true;
        } else {
            printf("✗ Failed to initialize embedded font\n");
        }
    } else {
        printf("No embedded font found\n");
    }

    // Try system font as fallback
    if (!success) {
        printf("Trying system font: /usr/share/fonts/ttf/noto/NotoMono-Regular.ttf\n");
        FILE* file = fopen("/usr/share/fonts/ttf/noto/NotoMono-Regular.ttf", "rb");
        if (file) {
            size_t bytes_read = fread(font_buffer, 1, sizeof(font_buffer), file);
            fclose(file);

            int result = stbtt_InitFont(&font, font_buffer, 0);
            if (result) {
                printf("✓ System font loaded successfully (%zu bytes)\n", bytes_read);
                success = true;
            } else {
                printf("✗ Failed to initialize system font\n");
            }
        } else {
            printf("✗ Could not open system font file\n");
        }
    }

    if (success) {
        printf("\n========================================\n");
        printf("Font Metrics:\n");
        printf("========================================\n");

        // Get font metrics
        int ascent, descent, lineGap;
        stbtt_GetFontVMetrics(&font, &ascent, &descent, &lineGap);

        printf("Ascent:  %d\n", ascent);
        printf("Descent: %d\n", descent);
        printf("LineGap: %d\n", lineGap);

        // Test rendering a character
        float scale = stbtt_ScaleForPixelHeight(&font, 24.0f);

        int advance, lsb;
        stbtt_GetCodepointHMetrics(&font, 'A', &advance, &lsb);

        printf("\nCharacter 'A' at 24px:\n");
        printf("  Advance: %.1f pixels\n", advance * scale);
        printf("  LSB:     %.1f pixels\n", lsb * scale);

        // Check if font uses outlines (CFF) or TrueType
        int x0, y0, x1, y1;
        stbtt_GetCodepointBitmapBox(&font, 'A', scale, scale, &x0, &y0, &x1, &y1);

        int width = x1 - x0;
        int height = y1 - y0;

        printf("  Bitmap:  %dx%d pixels\n", width, height);

        if (width > 0 && height > 0) {
            printf("\n✅ SUCCESS: Font will render filled glyphs\n");
            printf("   (TrueType outlines detected)\n");
        } else {
            printf("\n⚠  WARNING: Font may render as outlines only\n");
            printf("   (Possible CFF/PostScript outlines)\n");
            printf("   Convert OTF to TTF format!\n");
        }

        printf("\n========================================\n");
        return 0;
    } else {
        printf("\n✗ FAILED: Could not load any font\n");
        printf("\nTroubleshooting:\n");
        printf("  1. Make sure font is embedded in binary\n");
        printf("  2. Or ensure RM2 system font exists\n");
        printf("  3. Check font file is valid TTF/OTF\n");
        printf("\n========================================\n");
        return 1;
    }
}
