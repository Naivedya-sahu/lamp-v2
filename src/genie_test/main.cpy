#include "../resources/rmkit/src/build/rmkit.h"

using namespace std

// Simple genie test app - displays gesture feedback
class GestureTest:
  public:
  ui::Text *status_text
  ui::Scene scene

  GestureTest():
    // Create status text in center of screen
    scene = ui::make_scene()
    fb->clear_screen()
    fb->waveform_mode = WAVEFORM_MODE_DU

    status_text = new ui::Text(200, 800, 1000, 100, "Waiting for gesture...")
    status_text->set_style(ui::Stylesheet().font_size(48))
    scene->add(status_text)

  def handle_swipe_left():
    status_text->set_text("SWIPE LEFT detected!")
    scene->refresh()

  def handle_swipe_right():
    status_text->set_text("SWIPE RIGHT detected!")
    scene->refresh()

  def handle_swipe_up():
    status_text->set_text("SWIPE UP detected!")
    scene->refresh()

  def handle_swipe_down():
    status_text->set_text("SWIPE DOWN detected!")
    scene->refresh()

  def handle_two_finger_tap():
    status_text->set_text("TWO FINGER TAP detected!")
    scene->refresh()

  def run():
    ui::MainLoop::filter_palm_events = true
    ui::MainLoop::in.unmonitor(ui::MainLoop::in.wacom.fd)

    // Add gesture handlers
    auto swipe_left = [=](auto &ev) { this->handle_swipe_left(); }
    auto swipe_right = [=](auto &ev) { this->handle_swipe_right(); }
    auto swipe_up = [=](auto &ev) { this->handle_swipe_up(); }
    auto swipe_down = [=](auto &ev) { this->handle_swipe_down(); }
    auto two_tap = [=](auto &ev) { this->handle_two_finger_tap(); }

    ui::MainLoop::gestures.push_back({
      .name="swipe_left",
      .gesture_type=input::GESTURES::SWIPE_LEFT,
      .fingers=2,
      .on_gesture=swipe_left
    })

    ui::MainLoop::gestures.push_back({
      .name="swipe_right",
      .gesture_type=input::GESTURES::SWIPE_RIGHT,
      .fingers=2,
      .on_gesture=swipe_right
    })

    ui::MainLoop::gestures.push_back({
      .name="swipe_up",
      .gesture_type=input::GESTURES::SWIPE_UP,
      .fingers=2,
      .on_gesture=swipe_up
    })

    ui::MainLoop::gestures.push_back({
      .name="swipe_down",
      .gesture_type=input::GESTURES::SWIPE_DOWN,
      .fingers=2,
      .on_gesture=swipe_down
    })

    ui::MainLoop::gestures.push_back({
      .name="two_finger_tap",
      .gesture_type=input::GESTURES::TAP,
      .fingers=2,
      .on_gesture=two_tap
    })

    ui::MainLoop::refresh()
    ui::MainLoop::redraw()

    while true:
      ui::MainLoop::main()
      ui::MainLoop::redraw()
      ui::MainLoop::read_input()
      ui::MainLoop::handle_gestures()

def main():
  GestureTest app
  app.run()
