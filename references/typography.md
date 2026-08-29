# Multilingual typography contract

## Exact fonts

| Role | Contract | Matplotlib identity | Discovery |
|---|---|---|---|
| Latin text | Latin Modern Sans | `LMSans10` | exact `lmsans10-*.otf` files |
| mathematics | Latin Modern Math | `Latin Modern Math` | exact `latinmodern-math.otf` file |
| Simplified Chinese | Noto Sans CJK SC | same | exact family lookup, no fallback |
| Japanese | Noto Sans CJK JP | same | exact family lookup, no fallback |

This matches the Latin direction in `cigit-zgy/latex-templates`, whose current `typography.tex` selects `lmsans10-regular.otf` and `latinmodern-math.otf` explicitly.

On macOS, install the reproducible font packages with:

```bash
brew install --cask font-latin-modern font-latin-modern-math font-noto-sans-cjk-sc font-noto-sans-cjk-jp
fc-cache -f
python scripts/check_fonts.py
```

`discover_fonts()` registers the regular/bold/oblique/bold-oblique Latin files with Matplotlib, verifies the internal family identity, and uses `fallback_to_default=False` for CJK. Missing files, wrong internal names, or a family lookup that resolves to another font raise `FontContractError`.

## Mixed-language mapping

The language style provides an explicit ordered family list for ordinary labels. Mixed Chinese and Japanese strings must additionally use `font_for_language("zh")` and `font_for_language("ja")` so shared Han characters retain the correct regional glyph design. Math uses the custom MathText mapping to Latin Modern Math.

The required sample is `templates/multilingual.py`. Its final PDF must contain English `Nitrification efficiency`, Chinese `硝化效率`, Japanese `硝化効率`, and `mu_max`, `S_NH4`, `mg L^-1`, plus/minus, alpha, and beta symbols. Text extraction is a content check; rendered-page inspection remains the glyph-shape check.
