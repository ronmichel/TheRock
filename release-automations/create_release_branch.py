#!/usr/bin/env python3
"""
This script automates the creation of release branches for theRock projects and their submodules.
It supports branching from a specified source branch, including or excluding specific projects,
and optionally notifying stakeholders via email.

Main Features:
- Clones or uses an existing source tree for theRock and its submodules.
- Checks out the specified source branch for all relevant projects.
- Determines projects to branch based on .gitmodules and user input.
- Creates a plan for branching, including checks for branch existence and push permissions.
- Displays a summary of planned actions
- Executes branch creation and pushes to remote repositories.
- Sends notifications to specified email addresses.

Usage:
    python create_release_branch.py --release_branch <branch> [options]

Options:
    --release_branch         Name of the branch to create (required).
    --apitoken              API token for authentication with upstream repositories.
    --staging               Use staging environment.
    --prod                  Use production environment.
    --mailing_list          List of email addresses to notify.

Note:
    - This script assumes a specific repository structure and the presence of .gitmodules.
"""
import argparse
import configparser
import glob
import logging
import os
import shutil
import subprocess
import tempfile
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class rockbrachingAutomation():

    def __init__(self, args):
        
        self.release_branch = args.release_branch
        if args.apitoken:
            self.apitoken = args.apitoken
        else:
            self.apitoken = None
        self.is_staging = bool(args.staging)
        self.is_prod = bool(args.prod)
        
        if args.staging:
            self.gh_hostname = "github.amd.com"
            self.org = "ROCm-Staging"
        if args.prod:
            self.gh_hostname = "github.com"
            self.org = "ROCm"
        # Derive environment label for notifications
        if self.is_staging:
            self.environment = "Staging"
        elif self.is_prod:
            self.environment = "Prod"
        else:
            self.environment = "Unknown"
        
        if args.prod and args.staging:
            logging.error("You cannot pass both --staging(-S) and --prod(-P); choose one")
            exit(1)
        if args.mailing_list:
            self.mailing_list = args.mailing_list
        else:
            self.mailing_list = None


    # Helper function to run shell commands via subprocess.run.
    # Return exit_code and output (if capture_output is True).
    def run(self, cmd, cwd=None, capture_output=False, check=True):
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
        )
        if capture_output:
            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd)
            return (result.returncode, result.stdout.strip())
        else:
            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd)
            return (result.returncode, None)
        


    # Check out source code and returns a path to where theRock is checked out, projects dict, and
    def checkout_source(self):
        if self.is_staging and self.apitoken:
            the_rock_url = f"https://{self.apitoken}@{self.gh_hostname}/{self.org}/TheRock.git"
        else:
            the_rock_url = f"https://{self.gh_hostname}/{self.org}/TheRock.git"
        the_rock_dir_path = os.path.join(os.getcwd(), "TheRock")
        if os.path.isdir(the_rock_dir_path):
            logging.info("Removing existing TheRock directory for fresh clone")
            shutil.rmtree(the_rock_dir_path)
        logging.info("Cloning TheRock repository from %s", the_rock_url.replace(self.apitoken or '', '***'))
        self.run(f"git clone {the_rock_url}")
        cwd= os.getcwd()
        # Move into TheRock directory
        the_rock_dir = os.path.join(cwd, "TheRock")
        if not os.path.isdir(the_rock_dir):
            logging.error("TheRock directory not found after clone")
            raise RuntimeError("TheRock directory not found after clone")

        # Gather submodule info
        submodules = self.get_submodules(the_rock_dir)
        return the_rock_dir, submodules

    def get_submodules(self, repo_path):
        """Run 'git submodule status' and parse each line into a dict.
        Format of each line typically:
        <prefix><commit> <path> (description)
        Prefix: ' ' initialized, '-' not initialized, '+' updated.
        Store as: key=path, value={ 'commit': commit, 'prefix': prefix, 'description': description }
        """
        code, output = self.run("git submodule status", cwd=repo_path, capture_output=True, check=False)
        submodule_dict = {}
        if code != 0:
            return submodule_dict
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            # Example line: "d7f3c1e2c3c4abcd1234567890abcdef12345678 libs/rocBLAS (heads/main)"
            # With prefix: "-d7f3c1e ..."
            prefix = ''
            if line[0] in ['-', '+']:
                prefix = line[0]
                line = line[1:]
            parts = line.split()
            if len(parts) < 2:
                continue
            commit = parts[0]
            path = parts[1]
            description = ' '.join(parts[2:]) if len(parts) > 2 else ''
            # Store only the commit hash per user request (omit prefix and description)
            submodule_dict[path] = commit
        return submodule_dict



    # Determine projects to branch based on .gitmodules and user input.
    # This is a helper function for checkout_source.
    # Note that this returns a dict of project names to their key/value pairs from gitmodules.
    def determine_projects(self,  working_dir):
        logging.debug("Determining projects from gitmodules in %s", working_dir)
        gitmodules_path = os.path.join(working_dir, ".gitmodules")
        config = configparser.ConfigParser()
        config.read(gitmodules_path)
        projects = {}
        for section in config.sections():
            # Expect section like: submodule "path/to/project"
            if section.startswith('submodule '):
                raw_name = section[len('submodule '):]
                # Remove surrounding quotes if present
                name = raw_name.strip('"')
            else:
                name = section  # fallback
            projects[name] = {}
            for key, val in config.items(section):
                projects[name][key] = val
        return projects

    def get_upstream_branch(self, repo_path):
        """Return default upstream branch (main/master) with minimal checks."""
        # Try symbolic-ref first
        code, out = self.run(
            "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'",
            cwd=repo_path,
            capture_output=True,
            check=False,
        )
        if code == 0 and out.strip():
            return out.strip()
        # Simple fallbacks
        for branch in ("main", "master"):
            code, _ = self.run(
                f"git rev-parse --verify origin/{branch}",
                cwd=repo_path,
                capture_output=False,
                check=False,
            )
            if code == 0:
                return branch
        raise RuntimeError("Cannot determine upstream branch")


    # Update every yml file in the .github/workflows directory to replace source_branch with target_branch.
    def update_github_workflows(self, repo_path, source_branch, target_branch):
        workflow_dir = os.path.join(repo_path, ".github", "workflows")
        if not os.path.isdir(workflow_dir):
            return "No workflows found"

        yml_files = glob.glob(os.path.join(workflow_dir, "**"), recursive=True)
        updated_count = 0
        for yml_file in yml_files:
            if not yml_file.endswith((".yml", ".yaml")):
                continue
            try:
                with open(yml_file, "r", encoding="utf-8") as f:
                    content = f.read()
                pattern = f"- {source_branch}"
                replacement = f"- {target_branch}"
                if pattern in content:
                    # Replace only exact list item occurrences. This naive replace is acceptable
                    # because pattern includes leading dash+space. Avoid sed to handle slashes safely.
                    new_content = content.replace(pattern, replacement)
                    if new_content != content:
                        with open(yml_file, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        updated_count += 1
            except Exception as e:
                logging.warning("Failed updating %s: %s", yml_file, e)
        # Also update .gitmodules to set branch to target_branch for each submodule
        gitmodules_path = os.path.join(repo_path, ".gitmodules")
        if os.path.isfile(gitmodules_path):
            config = configparser.ConfigParser()
            config.read(gitmodules_path)
            changed = False
            for section in config.sections():
                if not config.has_option(section, "branch") or config.get(section, "branch") != target_branch:
                    config.set(section, "branch", target_branch)
                    changed = True
            if changed:
                with open(gitmodules_path, "w") as cfg:
                    config.write(cfg)
        return f"Updated {updated_count} workflow files and .gitmodules branches"

    def tokenize_url(self, url):
        """Embed token into https URL if token available."""
        if self.is_staging and self.apitoken and url.startswith('https://'):
            # Avoid double insertion
            if f'https://{self.apitoken}@' not in url:
                return url.replace('https://', f'https://{self.apitoken}@')
        return url

    # Execute the plan: clone each repo, create branch at commit, push to remote 'rocm-github'
    def execute_plan(self, plan, release_branch):
        temp_dir = tempfile.mkdtemp(prefix="rock-branching-")
        logging.info("Temporary working directory: %s", temp_dir)
        successful_components = {}
        failed_components = {}
        validation_components = {}
        for path_key, meta in plan.items():
            url = meta.get('url')
            commit = meta.get('commit')
            if not url or not commit:
                msg = f"Skipping {path_key}: missing url or commit"
                logging.warning(msg)
                failed_components[path_key] = {"error": msg}
                validation_components[path_key] = {
                    "status": "Failure",
                    "plan_commit": commit or "N/A",
                    "branch_commit": "N/A",
                }
                continue
            token_url = self.tokenize_url(url)
            repo_name = os.path.splitext(os.path.basename(url))[0]
            clone_dir = os.path.join(temp_dir, repo_name)
            logging.info("Cloning %s -> %s", url, clone_dir)
            try:
                self.run(f"git clone {token_url} {clone_dir}")
            except subprocess.CalledProcessError as e:
                err = f"Clone failed for {url}: {e}"
                logging.error(err)
                failed_components[path_key] = {"error": err}
                validation_components[path_key] = {
                    "status": "Failure",
                    "plan_commit": commit,
                    "branch_commit": "N/A",
                }
                continue
            # Add remote rocm-github (ignore error if exists)
            self.run(f"git remote add rocm-github {token_url}", cwd=clone_dir, check=False)
            # Create branch at commit id
            try:
                self.run(f"git checkout -b {release_branch} {commit}", cwd=clone_dir)
            except subprocess.CalledProcessError as e:
                err = f"Branch creation failed for {repo_name} at {commit}: {e}"
                logging.error(err)
                failed_components[path_key] = {"error": err}
                validation_components[path_key] = {
                    "status": "Failure",
                    "plan_commit": commit,
                    "branch_commit": "N/A",
                }
                continue
            # Push branch to rocm-github remote
            try:
                self.run(f"git push rocm-github {release_branch}", cwd=clone_dir)
                logging.info("Pushed %s for %s", release_branch, repo_name)
                successful_components[path_key] = {
                    "url": url,
                    "commit": commit,
                    "branch": release_branch,
                }
                # Validate branch head commit matches plan commit
                try:
                    _, branch_head = self.run(
                        f"git rev-parse {release_branch}",
                        cwd=clone_dir,
                        capture_output=True,
                        check=True,
                    )
                    status = "Success" if branch_head.strip() == commit else "Failure"
                    validation_components[path_key] = {
                        "status": status,
                        "plan_commit": commit,
                        "branch_commit": branch_head.strip(),
                    }
                except subprocess.CalledProcessError as e:
                    validation_components[path_key] = {
                        "status": "Failure",
                        "plan_commit": commit,
                        "branch_commit": f"Error: {e}",
                    }
            except subprocess.CalledProcessError as e:
                err = f"Push failed for {repo_name}: {e}"
                logging.error(err)
                failed_components[path_key] = {"error": err}
                validation_components[path_key] = {
                    "status": "Failure",
                    "plan_commit": commit,
                    "branch_commit": "N/A",
                }
        logging.info("Successful components: %s", successful_components)
        logging.info("Failed components: %s", failed_components)
        logging.info("Validation components: %s", validation_components)
        return successful_components, failed_components, validation_components

    def highlightCells(self, column):
        color = 'red'
        color1 = 'green'

        return [f'background-color: {color}' if cellvalue == 'Failure' or cellvalue == 'repo does not exist' else (f'background-color: {color1}' if cellvalue == 'Success' or cellvalue == 'admin' else '') for cellvalue in column ]

    def send_notifications(self, **kwargs):
        MAILING_LIST = kwargs.get('mailing_list')
        successful_components = kwargs.get('successful_components', {})
        failed_components = kwargs.get('failed_components', {})
        validation_components = kwargs.get('validation_components', {})
        if not MAILING_LIST:
            return

        styles = [
            {'selector': 'th', 'props': [('background', 'lightblue'), ('color', 'black'), ('text-align', 'left')]},
            {'selector': 'th, td', 'props': [('padding', '5px'), ('color', 'black'), ('text-align', 'left')]},
            {'selector': 'td', 'props': [('color', 'black'), ('text-align', 'left')]},
            {'selector': 'tr td:last-child', 'props': [('white-space', 'nowrap')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#bfeaf9')]},
        ]

        html_sections = []

        if successful_components:
            # Convert successful dict to a simpler table
            s_df = pd.DataFrame.from_dict(successful_components, orient='index').reset_index()
            # Expect columns: index, url, commit, branch
            s_df.columns = ["Component", "URL", "Commit", "Branch"]
            s_styled = s_df.style.set_table_attributes('border="1" class="dataframe table table-hover table-bordered"').set_table_styles(styles).hide()
            html_sections.append(f"<p><b>Successful Components</b></p>{s_styled.to_html()}")

        if failed_components:
            f_df = pd.DataFrame.from_dict(failed_components, orient='index').reset_index()
            f_df.columns = ["Component", "Error"]
            # Add a Status column for coloring
            f_df['Status'] = 'Failure'
            # Move Status to second column
            f_df = f_df[["Component", "Status", "Error"]]
            f_styled = f_df.style.apply(self.highlightCells, subset=['Status'], axis=0).set_table_attributes('border="1" class="dataframe table table-hover table-bordered"').set_table_styles(styles).hide()
            html_sections.append(f"<p><b>Failed Components</b></p>{f_styled.to_html()}")

        # Validation table: always most important
        if validation_components:
            v_df = pd.DataFrame.from_dict(validation_components, orient='index').reset_index()
            v_df.columns = ["Component", "Status", "Plan Commit", "Branch Commit"]
            v_styled = v_df.style.apply(self.highlightCells, subset=['Status'], axis=0).set_table_attributes('border="1" class="dataframe table table-hover table-bordered"').set_table_styles(styles).hide()
            html_sections.append(f"<p><b>Validation Table</b></p>{v_styled.to_html()}")
        
        header_msg = "Below is the branching status and commit validation for various Rock components:"  # placeholder
        html_body = "".join(html_sections) if html_sections else "<p>No components processed.</p>"
        html = f"<!DOCTYPE html><html><head></head><h4>{header_msg}</h4>{html_body}</html>"

        sender_email = "jenkins-compute@amd.com"
        recipients = [email.strip() for email in MAILING_LIST.split(',') if email.strip()]
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Branching Status Mail - {self.environment}".strip()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        part1 = MIMEText(html, "html")
        msg.attach(part1)
        try:
            s = smtplib.SMTP('torsmtp10.amd.com')
            s.send_message(msg)
            s.quit()
        except Exception as e:
            logging.error("Failed to send email: %s", e)

    def prepare_plan(self, projects, gitmodule_projects):
        """Compare two dictionaries:
        - projects: submodule dict mapping submodule path -> commit hash
        - gitmodule_projects: dict from .gitmodules with keys (project name) and values containing 'path' and 'url'
    Build a new dictionary where keys are matching submodule paths and values are dicts with URL and commit.
        """
        # Build quick lookup from path to url based on gitmodule_projects
        path_to_meta = {}
        for name, meta in gitmodule_projects.items():
            path_val = meta.get('path')
            if path_val:  # ensure path key exists
                path_to_meta[path_val] = meta.get('url')

        matched = {}
        for submodule_path, commit in projects.items():
            if submodule_path in path_to_meta:
                matched[submodule_path] = {
                    'url': path_to_meta[submodule_path],
                    'commit': commit,
                }
        return matched

    
    def main(self):
        working_dir, projects = self.checkout_source()
        self.update_github_workflows(working_dir, "main", self.release_branch)
        gitmodule_projects = self.determine_projects(working_dir)
        plan = self.prepare_plan(projects, gitmodule_projects)
        # Add TheRock itself using tip of its default/upstream branch
        try:
            default_branch = self.get_upstream_branch(working_dir)
            # Ensure we have latest
            self.run("git fetch origin", cwd=working_dir, check=False)
            _, root_commit = self.run(f"git rev-parse origin/{default_branch}", cwd=working_dir, capture_output=True, check=True)
        except Exception:
            # Fallback to current HEAD if upstream parsing fails
            _, root_commit = self.run("git rev-parse HEAD", cwd=working_dir, capture_output=True, check=True)
        if self.is_staging and self.apitoken:
            root_url = f"https://{self.apitoken}@{self.gh_hostname}/{self.org}/TheRock.git"
        else:
            root_url = f"https://{self.gh_hostname}/{self.org}/TheRock.git"
        plan['TheRock'] = { 'url': root_url, 'commit': root_commit }

        successfull_components, failed_components, validation_components = self.execute_plan(plan, self.release_branch)
        if self.mailing_list:
            logging.info(f"Branching completed. Sending notifications to: {self.mailing_list}")
            self.send_notifications(successful_components=successfull_components, failed_components=failed_components, validation_components=validation_components, mailing_list=self.mailing_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script for branching automation')
    parser.add_argument('-A', '--apitoken',
                        help='enter the api key to be used with the upstream repositories',
                        )
    parser.add_argument('-B', "--release_branch", required=True, help="Name of branch to create")
    parser.add_argument('-S', '--staging', action='store_true',
                        help='Pass this option to select staging environment',
                        )
    parser.add_argument('-P', '--prod', action='store_true',
                        help='Pass this option to select Prod environment',
                        )
    parser.add_argument('-M', '--mailing_list',
                        type=str,
                        help='Pass this option to provide comma separated list of mail-ids for notification',
                        )
    args = parser.parse_args()
    
    BranchObject = rockbrachingAutomation(args)
    BranchObject.main()
