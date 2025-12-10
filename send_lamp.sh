#!/bin/bash
#
# Send raw pen commands to lamp on reMarkable 2
# Uses SVG path data to draw symbols
#
# Usage: ./send_lamp.sh [RM2_IP]
#
# reMarkable 2 screen: 1404x1872 pixels

set -e

# Configuration
RM2_IP="${1:-10.11.99.1}"
LAMP="/opt/bin/lamp"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "SVG Path to Pen Commands"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Test connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo "Error: Cannot connect to $RM2_IP or lamp not found"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Function to send raw pen commands
send_pen_commands() {
    local pen_cmds="$1"
    ssh root@$RM2_IP "$LAMP" << 'EOF'
pen down 72 936
pen move 82 936
pen move 92 936
pen move 103 936
pen move 114 936
pen move 124 936
pen move 134 936
pen move 145 936
pen move 156 936
pen move 166 936
pen move 177 936
pen move 187 936
pen move 197 936
pen move 208 936
pen move 219 936
pen move 229 936
pen move 239 936
pen move 250 936
pen move 261 936
pen move 271 936
pen move 282 936
pen move 292 936
pen move 302 936
pen move 313 936
pen move 324 936
pen move 334 936
pen move 344 936
pen move 355 936
pen move 366 936
pen move 376 936
pen move 387 936
pen move 397 936
pen move 407 936
pen move 418 936
pen move 429 936
pen move 439 936
pen move 449 936
pen move 460 936
pen move 471 936
pen move 481 936
pen move 492 936
pen up
pen down 1052 936
pen move 1059 936
pen move 1066 936
pen move 1073 936
pen move 1080 936
pen move 1087 936
pen move 1094 936
pen move 1101 936
pen move 1108 936
pen move 1115 936
pen move 1122 936
pen move 1129 936
pen move 1136 936
pen move 1143 936
pen move 1150 936
pen move 1157 936
pen move 1164 936
pen move 1171 936
pen move 1178 936
pen move 1185 936
pen move 1192 936
pen move 1199 936
pen move 1206 936
pen move 1213 936
pen move 1220 936
pen move 1227 936
pen move 1234 936
pen move 1241 936
pen move 1248 936
pen move 1255 936
pen move 1262 936
pen move 1269 936
pen move 1276 936
pen move 1283 936
pen move 1290 936
pen move 1297 936
pen move 1304 936
pen move 1311 936
pen move 1318 936
pen move 1325 936
pen move 1332 936
pen up
pen down 1052 936
pen move 1037 943
pen move 1024 949
pen move 1009 957
pen move 996 963
pen move 982 971
pen move 967 978
pen move 954 984
pen move 939 992
pen move 926 998
pen move 912 1006
pen move 897 1013
pen move 884 1019
pen move 869 1027
pen move 856 1033
pen move 842 1041
pen move 827 1048
pen move 814 1054
pen move 799 1062
pen move 786 1068
pen move 772 1076
pen move 757 1083
pen move 744 1089
pen move 729 1097
pen move 716 1103
pen move 702 1111
pen move 687 1118
pen move 674 1124
pen move 659 1132
pen move 646 1138
pen move 632 1146
pen move 617 1153
pen move 604 1159
pen move 589 1167
pen move 576 1173
pen move 562 1181
pen move 547 1188
pen move 534 1194
pen move 519 1202
pen move 506 1208
pen move 492 1216
pen move 492 1202
pen move 492 1188
pen move 492 1173
pen move 492 1159
pen move 492 1146
pen move 492 1132
pen move 492 1118
pen move 492 1103
pen move 492 1089
pen move 492 1076
pen move 492 1062
pen move 492 1048
pen move 492 1033
pen move 492 1019
pen move 492 1006
pen move 492 992
pen move 492 978
pen move 492 963
pen move 492 949
pen move 492 936
pen move 492 922
pen move 492 908
pen move 492 893
pen move 492 879
pen move 492 866
pen move 492 852
pen move 492 838
pen move 492 823
pen move 492 809
pen move 492 796
pen move 492 782
pen move 492 767
pen move 492 754
pen move 492 739
pen move 492 726
pen move 492 712
pen move 492 697
pen move 492 684
pen move 492 669
pen move 492 656
pen move 506 662
pen move 519 669
pen move 534 677
pen move 547 684
pen move 562 691
pen move 576 697
pen move 589 704
pen move 604 712
pen move 617 719
pen move 632 726
pen move 646 732
pen move 659 739
pen move 674 747
pen move 687 754
pen move 702 761
pen move 716 767
pen move 729 774
pen move 744 782
pen move 757 789
pen move 772 796
pen move 786 802
pen move 799 809
pen move 814 817
pen move 827 823
pen move 842 831
pen move 856 838
pen move 869 844
pen move 884 852
pen move 897 858
pen move 912 866
pen move 926 873
pen move 939 879
pen move 954 887
pen move 967 893
pen move 982 901
pen move 996 908
pen move 1009 914
pen move 1024 922
pen move 1037 928
pen move 1052 936
pen up
pen down 1052 656
pen move 1052 669
pen move 1052 684
pen move 1052 697
pen move 1052 712
pen move 1052 726
pen move 1052 739
pen move 1052 754
pen move 1052 767
pen move 1052 782
pen move 1052 796
pen move 1052 809
pen move 1052 823
pen move 1052 838
pen move 1052 852
pen move 1052 866
pen move 1052 879
pen move 1052 893
pen move 1052 908
pen move 1052 922
pen move 1052 936
pen move 1052 949
pen move 1052 963
pen move 1052 978
pen move 1052 992
pen move 1052 1006
pen move 1052 1019
pen move 1052 1033
pen move 1052 1048
pen move 1052 1062
pen move 1052 1076
pen move 1052 1089
pen move 1052 1103
pen move 1052 1118
pen move 1052 1132
pen move 1052 1146
pen move 1052 1159
pen move 1052 1173
pen move 1052 1188
pen move 1052 1202
pen move 1052 1216
pen up
EOF
}

echo -e "${BLUE}Drawing R symbol...${NC}"

send_pen_commands

echo -e "${GREEN}✓ R symbol drawn${NC}"