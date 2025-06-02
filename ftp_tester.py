# Simple FTP tester for thinFTP
import ftplib
import os

# --- Configuration ---
# Replace with your FTP server details
FTP_HOST = "localhost"  # Or your server's IP address/hostname
FTP_PORT = 2528           # Default FTP port
FTP_USER = "your_username" # Replace with a test username
FTP_PASS = "your_password" # Replace with the test user's password

# --- Test file and directory names ---
TEST_DIR_NAME = "ftptest_dir_python"
TEST_FILE_NAME = "ftptest_file.txt"
TEST_FILE_CONTENT = "This is a test file for FTP STOR and RETR."
LOCAL_TEST_FILE_PATH = TEST_FILE_NAME # Will be created in the script's directory

def log_message(level, message):
    """Helper function for logging messages."""
    print(f"[{level.upper()}] {message}")

def create_local_test_file():
    """Creates a local dummy file for upload testing."""
    try:
        with open(LOCAL_TEST_FILE_PATH, "w") as f:
            f.write(TEST_FILE_CONTENT)
        log_message("info", f"Created local test file: {LOCAL_TEST_FILE_PATH}")
        return True
    except IOError as e:
        log_message("error", f"Failed to create local test file: {e}")
        return False

def remove_local_test_file():
    """Removes the local dummy file after testing."""
    try:
        if os.path.exists(LOCAL_TEST_FILE_PATH):
            os.remove(LOCAL_TEST_FILE_PATH)
            log_message("info", f"Removed local test file: {LOCAL_TEST_FILE_PATH}")
    except OSError as e:
        log_message("warning", f"Could not remove local test file {LOCAL_TEST_FILE_PATH}: {e}")

def run_ftp_tests():
    """Runs a series of FTP command tests."""
    ftp = None
    tests_passed = 0
    tests_failed = 0
    total_tests = 0

    if not create_local_test_file():
        log_message("error", "Aborting tests: Could not create local file for upload.")
        return

    test_results = []

    def record_test(command_name, success, details=""):
        nonlocal tests_passed, tests_failed, total_tests
        total_tests += 1
        status = "PASS" if success else "FAIL"
        test_results.append(f"Test: {command_name:<15} | Status: {status:<6} | Details: {details}")
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
        log_message("info" if success else "error", f"Command {command_name}: {status}. {details}")

    try:
        # --- 1. Connect and Login ---
        log_message("info", f"Attempting to connect to {FTP_HOST}:{FTP_PORT}...")
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST, FTP_PORT, timeout=10) # 10-second timeout
        log_message("info", "Connected.")
        record_test("CONNECT", True, f"Connected to {FTP_HOST}:{FTP_PORT}")

        try:
            ftp.login(FTP_USER, FTP_PASS)
            log_message("info", f"Logged in as {FTP_USER}.")
            record_test("USER/PASS", True, f"Login successful as {FTP_USER}")
        except ftplib.all_errors as e:
            record_test("USER/PASS", False, f"Login failed: {e}")
            raise Exception(f"Login failed, aborting further tests: {e}") # Abort if login fails

        # --- 2. Basic Information Commands ---
        try:
            syst_response = ftp.sendcmd('SYST')
            record_test("SYST", True, f"Server system type: {syst_response}")
        except ftplib.all_errors as e:
            record_test("SYST", False, f"SYST command failed: {e}")

        try:
            pwd_response = ftp.pwd()
            record_test("PWD", True, f"Initial working directory: {pwd_response}")
            initial_dir = pwd_response
        except ftplib.all_errors as e:
            record_test("PWD", False, f"PWD command failed: {e}")
            initial_dir = "/" # Fallback if PWD fails, though unlikely after login

        # --- 3. Set Transfer Type ---
        try:
            ftp.sendcmd('TYPE I') # Set to Binary/Image mode
            record_test("TYPE I", True, "Set transfer type to Binary (Image)")
        except ftplib.all_errors as e:
            record_test("TYPE I", False, f"TYPE I command failed: {e}")

        # --- 4. Passive Mode ---
        # PASV is generally preferred. EPSV is for IPv6 but often supported.
        passive_mode_set = False
        try:
            ftp.set_pasv(True) # Enable passive mode
            record_test("PASV/EPSV", True, "Passive mode enabled (using set_pasv)")
            passive_mode_set = True
        except ftplib.all_errors as e:
            record_test("PASV/EPSV", False, f"Failed to enable passive mode: {e}")
            log_message("warning", "Passive mode could not be set. Subsequent data transfer tests might fail.")


        if not passive_mode_set:
            log_message("warning", "Skipping data transfer tests as passive mode could not be established.")
        else:
            # --- 5. Directory Listing ---
            try:
                listing = ftp.nlst() # Names list
                record_test("NLST", True, f"NLST successful. Found {len(listing)} items.")
            except ftplib.all_errors as e:
                record_test("NLST", False, f"NLST command failed: {e}")

            try:
                # For LIST, ftplib's ftp.dir() captures output via callback
                dir_listing_lines = []
                ftp.dir(dir_listing_lines.append)
                record_test("LIST", True, f"LIST successful. Received {len(dir_listing_lines)} lines.")
            except ftplib.all_errors as e:
                record_test("LIST", False, f"LIST command failed: {e}")

            # --- 6. Directory Operations ---
            # MKD - Make Directory
            try:
                ftp.mkd(TEST_DIR_NAME)
                record_test("MKD", True, f"Created directory: {TEST_DIR_NAME}")
            except ftplib.all_errors as e:
                record_test("MKD", False, f"MKD command failed for {TEST_DIR_NAME}: {e}")
                # If MKD fails, CWD into it and RMD will also likely fail or be irrelevant.

            # CWD - Change Working Directory
            original_dir_for_cwd_test = ftp.pwd() # Get current dir before CWD
            try:
                ftp.cwd(TEST_DIR_NAME)
                new_pwd = ftp.pwd()
                if TEST_DIR_NAME in new_pwd: # Check if CWD was successful
                     record_test("CWD", True, f"Changed to directory: {new_pwd}")
                else:
                    record_test("CWD", False, f"CWD to {TEST_DIR_NAME} reported success, but PWD is {new_pwd}")
                ftp.cwd(original_dir_for_cwd_test) # Go back to original dir
                record_test("CWD (back)", True, f"Changed back to directory: {original_dir_for_cwd_test}")
            except ftplib.all_errors as e:
                record_test("CWD", False, f"CWD command failed for {TEST_DIR_NAME}: {e}")
                # Attempt to go back to initial directory if CWD failed partway
                try:
                    ftp.cwd(initial_dir)
                    log_message("info", f"Attempted to return to initial directory: {initial_dir}")
                except ftplib.all_errors:
                    log_message("warning", f"Could not return to initial directory {initial_dir} after CWD failure.")


            # --- 7. File Operations (inside the original directory) ---
            # Ensure we are in the initial directory for file operations
            try:
                current_pwd_before_file_ops = ftp.pwd()
                if initial_dir not in current_pwd_before_file_ops : # Check if we are in root or a known path
                    log_message("info", f"Changing to initial directory {initial_dir} before file operations.")
                    ftp.cwd(initial_dir)
            except ftplib.all_errors as e:
                log_message("error", f"Could not PWD or CWD to initial_dir before file ops: {e}. File ops may be affected.")


            # STOR - Store/Upload File
            stor_success = False
            try:
                with open(LOCAL_TEST_FILE_PATH, 'rb') as f:
                    ftp.storbinary(f'STOR {TEST_FILE_NAME}', f)
                record_test("STOR", True, f"Uploaded file: {TEST_FILE_NAME}")
                stor_success = True
            except ftplib.all_errors as e:
                record_test("STOR", False, f"STOR command failed for {TEST_FILE_NAME}: {e}")

            # RETR - Retrieve/Download File
            if stor_success: # Only try to retrieve if upload was successful
                local_download_path = "downloaded_" + TEST_FILE_NAME
                try:
                    with open(local_download_path, 'wb') as f:
                        ftp.retrbinary(f'RETR {TEST_FILE_NAME}', f.write)
                    # Verify content (optional, basic check here)
                    with open(local_download_path, 'r') as f_downloaded, open(LOCAL_TEST_FILE_PATH, 'r') as f_original:
                        if f_downloaded.read() == f_original.read():
                            record_test("RETR", True, f"Downloaded and verified file: {TEST_FILE_NAME}")
                        else:
                            record_test("RETR", False, f"Downloaded file {TEST_FILE_NAME}, but content mismatch.")
                    if os.path.exists(local_download_path): os.remove(local_download_path)
                except ftplib.all_errors as e:
                    record_test("RETR", False, f"RETR command failed for {TEST_FILE_NAME}: {e}")
                    if os.path.exists(local_download_path): os.remove(local_download_path) # Clean up partial download
            else:
                record_test("RETR", False, "Skipped (STOR failed)")


            # DELE - Delete File
            if stor_success: # Only try to delete if upload was successful
                try:
                    ftp.delete(TEST_FILE_NAME)
                    record_test("DELE", True, f"Deleted remote file: {TEST_FILE_NAME}")
                except ftplib.all_errors as e:
                    record_test("DELE", False, f"DELE command failed for {TEST_FILE_NAME}: {e}")
            else:
                record_test("DELE", False, "Skipped (STOR failed or file not present)")


            # --- 8. Cleanup Directory (RMD) ---
            # RMD - Remove Directory (only if MKD was successful)
            # Check if TEST_DIR_NAME is in the listing before attempting RMD
            dir_exists_for_rmd = False
            try:
                if TEST_DIR_NAME in ftp.nlst():
                    dir_exists_for_rmd = True
            except ftplib.all_errors:
                log_message("warning", "Could not list directory contents before RMD.")

            if dir_exists_for_rmd:
                try:
                    ftp.rmd(TEST_DIR_NAME)
                    record_test("RMD", True, f"Removed directory: {TEST_DIR_NAME}")
                except ftplib.all_errors as e:
                    record_test("RMD", False, f"RMD command failed for {TEST_DIR_NAME}: {e} (Directory might not be empty or MKD failed)")
            else:
                 record_test("RMD", False, f"Skipped (Directory {TEST_DIR_NAME} not found or MKD failed)")


        # --- 9. NOOP ---
        try:
            ftp.voidcmd('NOOP')
            record_test("NOOP", True, "NOOP command successful")
        except ftplib.all_errors as e:
            record_test("NOOP", False, f"NOOP command failed: {e}")

    except ftplib.all_errors as e:
        log_message("critical", f"A critical FTP error occurred: {e}")
        if total_tests == 0 : # If connect failed
             record_test("CONNECT", False, f"Connection failed: {e}")
        elif "USER/PASS" not in [res.split("|")[0].split(":")[1].strip() for res in test_results if "USER/PASS" in res]: # If login failed
            # This case is handled by the explicit raise after login failure
            pass
        else:
            record_test("CRITICAL_ERROR", False, f"An unhandled FTP error occurred: {e}")


    finally:
        # --- 10. QUIT ---
        if ftp:
            try:
                ftp.quit()
                record_test("QUIT", True, "QUIT command successful, connection closed.")
                log_message("info", "Connection closed.")
            except ftplib.all_errors as e:
                record_test("QUIT", False, f"QUIT command failed: {e}")
                log_message("error", f"Error during QUIT: {e}")
            ftp = None # Ensure ftp object is cleared

        remove_local_test_file()

        # --- Print Summary ---
        print("\n--- Test Summary ---")
        for result_line in test_results:
            print(result_line)
        print("--------------------")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {tests_passed}")
        print(f"Failed: {tests_failed}")
        print("--------------------")

if __name__ == "__main__":
    # --- User Input for FTP Details ---
    host_input = input(f"Enter FTP Host (default: {FTP_HOST}): ") or FTP_HOST
    port_input_str = input(f"Enter FTP Port (default: {FTP_PORT}): ")
    try:
        port_input = int(port_input_str) if port_input_str else FTP_PORT
    except ValueError:
        print(f"Invalid port number. Using default: {FTP_PORT}")
        port_input = FTP_PORT

    user_input = input(f"Enter FTP Username (default: {FTP_USER}): ") or FTP_USER
    pass_input = input(f"Enter FTP Password: ") # No default for password for security

    FTP_HOST = host_input
    FTP_PORT = port_input
    FTP_USER = user_input
    FTP_PASS = pass_input

    run_ftp_tests()

