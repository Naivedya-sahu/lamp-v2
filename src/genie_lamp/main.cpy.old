#include <cstddef>
#include <fstream>

#include "../build/rmkit.h"
#include "../shared/string.h"

#include "gesture_parser.h"

INFILE := "genie_lamp.conf"
using namespace std
using namespace genie

class App:
  public:
  def run():
    // Don't listen for stylus events, saves CPU
    ui::MainLoop::in.unmonitor(ui::MainLoop::in.wacom.fd)

    // Main event loop - no framebuffer refresh needed
    while true:
      ui::MainLoop::main()
      ui::MainLoop::read_input()
      ui::MainLoop::handle_gestures()

HAS_GESTURES := false
def setup_gestures(App &app, string filename):
  string line
  ifstream infile(filename)
  vector<string> lines

  while getline(infile, line):
    lines.push_back(line)

  gestures := parse_config(lines)
  if gestures.size() > 0:
    HAS_GESTURES = true
  else:
    debug "NO GESTURES IN", filename
    return

  for auto g : gestures:
    ui::MainLoop::gestures.push_back(g)

def main(int argc, char **argv):
  App app

  if argc > 1:
    INFILE = argv[1]

  setup_gestures(app, INFILE)

  if not HAS_GESTURES:
    debug "NO GESTURES FOUND, PLEASE SET SOME UP"
    exit(0)

  debug "GENIE_LAMP STARTED - NO RM2FB REQUIRED"
  app.run()
