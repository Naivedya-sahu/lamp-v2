# rm2fb (reMarkable 2 Framebuffer) Notes

## What is rm2fb?

The reMarkable 2 uses a special framebuffer interface that requires `rm2fb` (remarkable2-framebuffer) for many applications to work correctly.

## Installation on RM2

### Option 1: Via Toltec (Recommended)
```bash
# On RM2
opkg update
opkg install rm2fb
systemctl enable --now rm2fb
```

### Option 2: Manual
```bash
# Build from source (in resources/rm2fb)
cd resources/rm2fb
make
# Copy to RM2
scp rm2fb root@10.11.99.1:/opt/bin/
ssh root@10.11.99.1
chmod +x /opt/bin/rm2fb
/opt/bin/rm2fb &
```

## Apps That Need rm2fb

### Full rmkit Apps (Need rm2fb):
- `genie_test` - Uses rmkit UI framework
- `symbol_selector` - Uses rmkit UI framework (WIP)

**Workaround:** Run with rm2fb client wrapper:
```bash
# Make sure rm2fb is running on RM2
systemctl status rm2fb

# Run app normally
./genie_test
```

### Standalone Apps (No rm2fb needed):
- `font_test` - Simple validation, uses stb_truetype only
- `lamp` - Direct pen command system
- Component rendering scripts

## Troubleshooting

**Error: "cannot open /dev/fb0"**
→ rm2fb not running. Install and start rm2fb service.

**Error: "rm2fb: Connection refused"**
→ rm2fb service not started: `systemctl start rm2fb`

**Apps don't display anything**
→ Check rm2fb is active: `systemctl status rm2fb`
→ Try restarting: `systemctl restart rm2fb`

## Reference

- rm2fb GitHub: https://github.com/ddvk/remarkable2-framebuffer
- Toltec repository: https://toltec-dev.org/
- rmkit documentation: https://rmkit.dev/

## Build Without rm2fb

To avoid rm2fb dependency:
1. Use `lamp` direct pen commands (like `draw_component.sh`)
2. Use framebuffer-free tools (like `font_test`)
3. Or ensure rm2fb is installed on target RM2 device
