# Get information about members in the group (replace glpat-hyuxjcbthe4vJMtcjsGs with your token)
members_info=$(curl --header "PRIVATE-TOKEN: $PRIVATE_TOKEN" "https://git-switch.parswitch.org/api/v4/groups/5/members")

# Use the value of $GITLAB_USER_LOGIN as the target username
target_username="$GITLAB_USER_LOGIN"


# Find the user information and extract the access_level
access_level=$(echo "$members_info" | jq -r '.[] | select(.username == "'"$target_username"'") | .access_level')

# Print the access level
echo "Access Level for $target_username: $access_level"

# Check access level and cancel pipeline if it's under 40
if [ "$access_level" -lt 40 ]; then
  echo "Access level is under 40. Cancelling the pipeline."
  exit 1
fi