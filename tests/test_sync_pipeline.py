import types
import unittest

import main


class DummySSH:
    def __init__(self, host):
        self.host = host

    def close(self):
        return None


class DummyPopup:
    def __init__(self):
        self.status_log = []

    def update_status(self, message, progress, stage):
        self.status_log.append((message, progress, stage))

    def close_with_delay(self, delay=0):
        return None

    def destroy(self):
        return None


class DummyWidget:
    def configure(self, **kwargs):
        return None

    def stop(self):
        return None

    def set(self, value):
        return None

    def delete(self, *args, **kwargs):
        return None


class FakePC:
    def __init__(self, pc_name, host_name, user_name, password, path_files):
        self.pc_name = pc_name
        self.host_name = host_name
        self.user_name = user_name
        self.password = password
        self.pathFiles = path_files

    def __hash__(self):
        return hash((self.pc_name, self.host_name))


class SyncPipelineFlowTest(unittest.TestCase):
    def test_processes_all_diff_folders_and_all_same_path_repos_per_pc(self):
        pc1 = FakePC(
            pc_name="PC-1",
            host_name="10.0.0.1",
            user_name="user",
            password="pass",
            path_files={
                0: {"inputfolder": "C:\\A", "OutputDir": "D:\\Repo", "FileType": "ALL"},
                1: {"inputfolder": "C:\\B", "OutputDir": "D:\\Repo", "FileType": "ALL"},
            },
        )
        pc2 = FakePC(
            pc_name="PC-2",
            host_name="10.0.0.2",
            user_name="user",
            password="pass",
            path_files={
                0: {"inputfolder": "C:\\C", "OutputDir": "D:\\Repo", "FileType": "ALL"},
            },
        )

        counters = {
            "fetch": 0,
            "compare": 0,
            "apply": 0,
            "check_status": 0,
            "commit": 0,
            "push": 0,
            "success": 0,
        }

        fake = types.SimpleNamespace()
        fake.checked_Pc_objs = [pc1, pc2]
        fake._enqueue_ui = lambda fn: fn()
        fake._sync_ui_status = lambda popup, msg, prog, stage: popup.update_status(msg, prog, stage)
        fake._display_path = lambda p: p
        fake._wait_for_folder_diff_confirmation = lambda folder_diffs, err: True
        fake._wait_for_commit_confirmation = lambda diffs, err: True
        fake.create_ssh_connection = lambda host, user, password: DummySSH(host)
        fake.check_destination_git_before_sync_remote = lambda ssh, output_dir: ("D:\\Repo", None)
        fake.get_current_branch_remote = lambda ssh, repo_path: "main"

        def remote_fetch_and_pull(ssh, repo_path, branch):
            counters["fetch"] += 1
            return True

        def compare_folders_remote(ssh, source, dest, file_type):
            counters["compare"] += 1
            return {f"{source}\\file.txt": {"file": "file.txt", "type": "New"}}

        def apply_folder_diffs_remote(ssh, source_folder, destination_folder, diffs):
            counters["apply"] += 1
            return len(diffs)

        def check_repo_status_remote(ssh, repo_path):
            counters["check_status"] += 1
            return True, {"x": {"file": "x", "type": "modified"}}

        def commit_remote(ssh, repo_path, branch, message):
            counters["commit"] += 1
            return True

        def push_remote(ssh, repo_path, branch):
            counters["push"] += 1
            return True

        def sync_pipeline_success(err_label, commit_box, popup):
            counters["success"] += 1

        def sync_pipeline_error(text, err_label, commit_box, popup, ssh_client=None):
            raise AssertionError(f"Pipeline raised error: {text}")

        fake.remote_fetch_and_pull = remote_fetch_and_pull
        fake.count_only_files = lambda ssh, input_folder, file_type="ALL": 1
        fake.find_nearest_git_root_remote = lambda ssh, out: "D:\\Repo"
        fake.compare_folders_remote = compare_folders_remote
        fake.apply_folder_diffs_remote = apply_folder_diffs_remote
        fake.check_repo_status_remote = check_repo_status_remote
        fake.commit_remote = commit_remote
        fake.push_remote = push_remote
        fake._sync_pipeline_success = sync_pipeline_success
        fake._sync_pipeline_error = sync_pipeline_error
        fake.git_progressbar = DummyWidget()
        fake.block_dropdown = DummyWidget()
        fake.not_using_param_checkbox = DummyWidget()

        popup = DummyPopup()
        err_label = DummyWidget()
        commit_box = DummyWidget()

        count = main.LabSyncDashBoard._run_git_sync_pipeline(
            fake,
            popup,
            err_label,
            commit_box,
            "test commit",
        )

        self.assertEqual(count, 3)
        self.assertEqual(counters["compare"], 3)
        self.assertEqual(counters["apply"], 3)
        self.assertEqual(counters["fetch"], 2)
        self.assertEqual(counters["check_status"], 2)
        self.assertEqual(counters["commit"], 2)
        self.assertEqual(counters["push"], 2)
        self.assertEqual(counters["success"], 1)

    def test_handles_large_diff_with_new_and_deleted_folder_trees(self):
        pc1 = FakePC(
            pc_name="PC-1",
            host_name="10.0.0.1",
            user_name="user",
            password="pass",
            path_files={
                0: {"inputfolder": "C:\\HugeSource", "OutputDir": "D:\\Repo", "FileType": "ALL"},
            },
        )

        large_diffs = {}
        for i in range(6000):
            rel = f"new_root\\batch_{i // 1000}\\sub_{i % 10}\\file_{i:04d}.txt"
            large_diffs[rel] = {"file": rel, "type": "New"}
        for i in range(120):
            rel = f"old_root\\legacy_{i % 6}\\nested_{i % 4}\\old_{i:03d}.txt"
            large_diffs[rel] = {"file": rel, "type": "Deleted"}

        counters = {
            "fetch": 0,
            "compare": 0,
            "apply": 0,
            "check_status": 0,
            "commit": 0,
            "push": 0,
            "success": 0,
        }
        seen = {"new": 0, "deleted": 0, "has_new_tree": False, "has_deleted_tree": False}

        fake = types.SimpleNamespace()
        fake.checked_Pc_objs = [pc1]
        fake._enqueue_ui = lambda fn: fn()
        fake._sync_ui_status = lambda popup, msg, prog, stage: popup.update_status(msg, prog, stage)
        fake._display_path = lambda p: p
        fake._wait_for_folder_diff_confirmation = lambda folder_diffs, err: True
        fake._wait_for_commit_confirmation = lambda diffs, err: True
        fake.create_ssh_connection = lambda host, user, password: DummySSH(host)
        fake.check_destination_git_before_sync_remote = lambda ssh, output_dir: ("D:\\Repo", None)
        fake.get_current_branch_remote = lambda ssh, repo_path: "main"

        def remote_fetch_and_pull(ssh, repo_path, branch):
            counters["fetch"] += 1
            return True

        def compare_folders_remote(ssh, source, dest, file_type):
            counters["compare"] += 1
            return large_diffs

        def apply_folder_diffs_remote(ssh, source_folder, destination_folder, diffs):
            counters["apply"] += 1
            for rel_path, info in diffs.items():
                status = info["type"].lower()
                if status == "new":
                    seen["new"] += 1
                if status == "deleted":
                    seen["deleted"] += 1
                if rel_path.startswith("new_root\\"):
                    seen["has_new_tree"] = True
                if rel_path.startswith("old_root\\"):
                    seen["has_deleted_tree"] = True
            return len(diffs)

        def check_repo_status_remote(ssh, repo_path):
            counters["check_status"] += 1
            return True, {"x": {"file": "x", "type": "modified"}}

        def commit_remote(ssh, repo_path, branch, message):
            counters["commit"] += 1
            return True

        def push_remote(ssh, repo_path, branch):
            counters["push"] += 1
            return True

        def sync_pipeline_success(err_label, commit_box, popup):
            counters["success"] += 1

        def sync_pipeline_error(text, err_label, commit_box, popup, ssh_client=None):
            raise AssertionError(f"Pipeline raised error: {text}")

        fake.remote_fetch_and_pull = remote_fetch_and_pull
        fake.count_only_files = lambda ssh, input_folder, file_type="ALL": len(large_diffs)
        fake.find_nearest_git_root_remote = lambda ssh, out: "D:\\Repo"
        fake.compare_folders_remote = compare_folders_remote
        fake.apply_folder_diffs_remote = apply_folder_diffs_remote
        fake.check_repo_status_remote = check_repo_status_remote
        fake.commit_remote = commit_remote
        fake.push_remote = push_remote
        fake._sync_pipeline_success = sync_pipeline_success
        fake._sync_pipeline_error = sync_pipeline_error
        fake.git_progressbar = DummyWidget()
        fake.block_dropdown = DummyWidget()
        fake.not_using_param_checkbox = DummyWidget()

        popup = DummyPopup()
        err_label = DummyWidget()
        commit_box = DummyWidget()

        count = main.LabSyncDashBoard._run_git_sync_pipeline(
            fake,
            popup,
            err_label,
            commit_box,
            "test commit",
        )

        self.assertEqual(count, len(large_diffs))
        self.assertEqual(counters["compare"], 1)
        self.assertEqual(counters["apply"], 1)
        self.assertEqual(counters["fetch"], 1)
        self.assertEqual(counters["check_status"], 1)
        self.assertEqual(counters["commit"], 1)
        self.assertEqual(counters["push"], 1)
        self.assertEqual(counters["success"], 1)
        self.assertEqual(seen["new"], 6000)
        self.assertEqual(seen["deleted"], 120)
        self.assertTrue(seen["has_new_tree"])
        self.assertTrue(seen["has_deleted_tree"])


class FakeChannel:
    def __init__(self, code=0):
        self._code = code

    def recv_exit_status(self):
        return self._code


class FakeStream:
    def __init__(self, text="", code=0):
        self._data = text.encode("utf-8")
        self.channel = FakeChannel(code)

    def read(self):
        return self._data


class CapturingSSH:
    def __init__(self):
        self.commands = []

    def exec_command(self, command):
        self.commands.append(command)
        if "Write-Output ('COPIED=" in command:
            return None, FakeStream("COPIED=1;DELETED=1", 0), FakeStream("", 0)
        return None, FakeStream("", 0), FakeStream("", 0)


class ApplyFolderDiffBehaviorTest(unittest.TestCase):
    def test_apply_folder_diffs_requests_empty_folder_cleanup(self):
        fake_ssh = CapturingSSH()
        diffs = {
            "new_root\\a\\new_file.txt": {"file": "new_root\\a\\new_file.txt", "type": "New"},
            "old_root\\b\\old_file.txt": {"file": "old_root\\b\\old_file.txt", "type": "Deleted"},
        }

        result = main.LabSyncDashBoard.apply_folder_diffs_remote(
            types.SimpleNamespace(),
            fake_ssh,
            source_folder="C:\\Src",
            destination_folder="D:\\Repo",
            diffs=diffs,
        )

        self.assertGreaterEqual(result, 2)
        cleanup_commands = [
            cmd
            for cmd in fake_ssh.commands
            if "Get-ChildItem -Path 'D:\\Repo' -Recurse -Directory" in cmd
            and "Remove-Item -Force" in cmd
        ]
        self.assertGreaterEqual(len(cleanup_commands), 1)


if __name__ == "__main__":
    unittest.main()
