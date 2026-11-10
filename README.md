# Markdown to PDF Editor (Presswork PDF)

A free Windows app that opens Markdown (`.md`) files, shows them with full formatting, and exports
real PDF files in **A4 or A3**, **portrait or landscape**.

- Formatted reading view on a paper-sized page, with page breaks
- Zoom: **Ctrl + mouse wheel**, Ctrl +/-, Ctrl+0 (fit), Ctrl+1 (100%)
- Export the current choice, or all four size/orientation combinations at once
- Accent colour and margin options
- Tables, code blocks, lists, quotes, images (relative paths), links
- "Open .md files with this app" button, so a double-click opens a file here
- Works offline

## Use it

1. Download `PressworkPDF.exe` from the [Releases](../../releases) page, or run from source (below).
2. Click **Open .md file...**, pick paper size and orientation, then **Export PDF...**.

Needs Windows 10/11 with Microsoft Edge (and its WebView2 runtime), which are already installed on
most PCs. Edge is also what writes the PDF, in the background.

## Run from source

```
pip install -r requirements.txt
python presswork_pdf.py [file.md]
```

Build your own exe with `build.bat`.

## Notes

- PDF names look like `26_1110_report_A3_landscape.pdf` (date, name, size, orientation).
- Fonts: uses Fraunces / Source Serif if installed, otherwise Palatino / Georgia.
- Windows may show a SmartScreen warning for the unsigned exe: choose "More info" > "Run anyway".

## License

MIT - see [LICENSE](LICENSE). Third-party notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
