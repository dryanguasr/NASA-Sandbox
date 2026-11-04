#!/usr/bin/env bash
# Send separate movement commands and stop all agents on exit.
set -euo pipefail
send() { gz topic -t "/model/$1/cmd_vel" -m gz.msgs.Twist -p "$2"; }
stop_all() {
  for id in human_1 human_2 rover_1 rover_2 drone_1 drone_2; do
    send "$id" 'linear: {x: 0, y: 0, z: 0}, angular: {z: 0}' || true
  done
}
trap stop_all EXIT
# Verify each controller independently before the combined phase.
for id in human_1 human_2 rover_1 rover_2 drone_1 drone_2; do
  echo "Individual control: $id"
  send "$id" 'linear: {x: 0.08}'
  sleep 2
  send "$id" 'linear: {x: 0, y: 0, z: 0}, angular: {z: 0}'
  sleep 1
done
echo 'Combined control'
send human_1 'linear: {x: 0.05}'
send human_2 'linear: {y: 0.05}'
send rover_1 'linear: {x: 0.20}, angular: {z: 0.05}'
send rover_2 'linear: {x: 0.18}, angular: {z: -0.05}'
send drone_1 'linear: {z: 0.08}'
send drone_2 'linear: {x: 0.08}'
sleep 3
