name: git-profile-koi
description:
  Draw a GitHub account's koi from its public activity as a looping GIF, a still
  PNG, and a preview, for a profile README.
branding:
  icon: droplet
  color: blue

inputs:
  login:
    description: Account whose koi to draw.
    default: ${{ github.repository_owner }}
  body:
    description: Body color, one of white, black, asagi, tea, gold, or platinum.
    default: white
  output-dir:
    description:
      Folder, relative to the workspace, that receives koi.gif, koi.png, and
      preview.html.
    default: koi
  token:
    description:
      Token for reading the account's public data; the built-in token is enough.
    default: ${{ github.token }}

runs:
  using: composite
  steps:
    - name: Download the git-koi release this Action belongs to
      shell: bash
      env:
        GH_TOKEN: ${{ inputs.token }}
      run: |
        version=$(grep -m1 '^version' "$GITHUB_ACTION_PATH/Cargo.toml" | cut -d'"' -f2)
        repository=$(grep -m1 '^repository' "$GITHUB_ACTION_PATH/Cargo.toml" | cut -d'"' -f2)
        case "$RUNNER_OS-$RUNNER_ARCH" in
          Linux-X64) target=x86_64-unknown-linux-musl ;;
          Linux-ARM64) target=aarch64-unknown-linux-musl ;;
          macOS-X64) target=x86_64-apple-darwin ;;
          macOS-ARM64) target=aarch64-apple-darwin ;;
          *)
            echo "git-koi has no build for $RUNNER_OS $RUNNER_ARCH; use ubuntu-latest" >&2
            exit 1
            ;;
        esac
        archive="git-koi-$version-$target.tar.gz"
        install_dir="$RUNNER_TEMP/git-koi"
        mkdir -p "$install_dir"
        if ! gh release download "v$version" --repo "$repository" --dir "$install_dir" \
            --pattern "$archive" --pattern "$archive.sha256"; then
          echo "release v$version has no asset $archive; reference the Action at a release tag" >&2
          exit 1
        fi
        cd "$install_dir"
        if command -v sha256sum > /dev/null; then
          sha256sum -c "$archive.sha256"
        else
          shasum -a 256 -c "$archive.sha256"
        fi
        tar -xzf "$archive"
        echo "$install_dir/git-koi-$version-$target" >> "$GITHUB_PATH"
    - name: Collect the account snapshot
      shell: bash
      env:
        GH_TOKEN: ${{ inputs.token }}
        KOI_LOGIN: ${{ inputs.login }}
      run:
        git-koi collect "$KOI_LOGIN" --output "$RUNNER_TEMP/koi-snapshot.json"
    - name: Render the koi
      shell: bash
      env:
        KOI_BODY: ${{ inputs.body }}
        KOI_OUTPUT_DIR: ${{ inputs.output-dir }}
      run:
        git-koi render "$RUNNER_TEMP/koi-snapshot.json" --output-dir
        "$KOI_OUTPUT_DIR" --body "$KOI_BODY"
