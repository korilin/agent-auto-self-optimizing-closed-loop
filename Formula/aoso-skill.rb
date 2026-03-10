class AosoSkill < Formula
  include Language::Python::Virtualenv

  desc "CLI for initializing and operating the AOSO self-optimizing skill"
  homepage "https://github.com/korilin/agent-auto-self-optimizing-closed-loop"
  url "https://github.com/korilin/agent-auto-self-optimizing-closed-loop.git",
      branch: "main"
  version "0.1.2"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "aoso-skill", shell_output("#{bin}/aoso-skill help")
  end
end
