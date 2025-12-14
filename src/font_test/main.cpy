#include "../resources/rmkit/src/build/rmkit.h"

using namespace std

// Simple font test - renders sample text at various sizes
class FontTest:
  public:
  ui::Scene scene
  vector<ui::Text*> labels

  FontTest():
    scene = ui::make_scene()
    fb->clear_screen()
    fb->waveform_mode = WAVEFORM_MODE_GC16

    // Title
    auto title = new ui::Text(100, 100, 1200, 100, "Font Rendering Test")
    title->set_style(ui::Stylesheet().font_size(48).font_weight(900))
    scene->add(title)
    labels.push_back(title)

    // Test different sizes
    int y_pos = 250
    vector<int> sizes = {16, 24, 32, 48, 64}
    for auto size : sizes:
      string text = "Size " + to_string(size) + ": ABCDEFG 12345 !@#$%"
      auto label = new ui::Text(100, y_pos, 1200, size + 20, text)
      label->set_style(ui::Stylesheet().font_size(size))
      scene->add(label)
      labels.push_back(label)
      y_pos += size + 40

    // Instructions at bottom
    auto info = new ui::Text(100, 1700, 1200, 100, "Text should be FILLED (solid black), not outlined")
    info->set_style(ui::Stylesheet().font_size(24))
    scene->add(info)
    labels.push_back(info)

  def run():
    ui::MainLoop::filter_palm_events = true
    ui::MainLoop::in.unmonitor(ui::MainLoop::in.wacom.fd)

    ui::MainLoop::refresh()
    ui::MainLoop::redraw()

    // Simple event loop - exit on any touch
    bool running = true
    while running:
      ui::MainLoop::main()
      ui::MainLoop::redraw()
      ui::MainLoop::read_input()

      // Exit on touch
      if ui::MainLoop::in.touch.ev.size() > 0:
        running = false

    fb->clear_screen()
    fb->waveform_mode = WAVEFORM_MODE_DU
    ui::MainLoop::refresh()

def main():
  FontTest app
  app.run()
