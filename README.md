systemctl --user import-environment DISPLAY XAUTHORITY
dbus-update-activation-environment DISPLAY XAUTHORITY
setxkbmap -option
systemctl --user restart send-url.service
systemctl --user restart latch-lock-show.service
systemctl --user restart latch-lock-run.service
sleep 1
setxkbmap -option caps:none
setxkbmap -option compose:menu
xinput --set-prop "ASUE1211:00 04F3:3211 Touchpad" "libinput Tapping Enabled" 1
setxkbmap -layout us,cz -variant basic,qwerty -option grp:alt_shift_toggle
