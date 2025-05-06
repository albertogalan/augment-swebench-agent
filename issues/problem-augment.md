[GOAL]
need to integrate deepseek llm model on cli.py


[PROBLEM]

Add this feature on utils/swerex_wrapper.py

I need to use dynamically different interactive environments
 like ipython, gdb, mysql client, etc. in the same session

put in config.toml command with the command to execute

[CONTEXT]
if you need full test
python cli.py --workspace /Users/agalan/data/src/wk/fibbonacci    --problem-statement "please check the quadratic function is working"


[DOCUMENTATION]

# Interactive Command Line Tools in SWE-ReX

Here's a list of different interactive command line tools you could use with SWE-ReX, along with example commands to start them in a session:

1. **IPython** - Interactive Python shell
   ```python
   await runtime.run_in_session(BashAction(command="ipython", session_id=session_id))
   ```

2. **GDB** - GNU Debugger
   ```python
   await runtime.run_in_session(BashAction(command="gdb ./myprogram", session_id=session_id))
   ```

3. **MySQL Client**
   ```python
   await runtime.run_in_session(BashAction(command="mysql -u username -p", session_id=session_id))
   ```

4. **PostgreSQL Client**
   ```python
   await runtime.run_in_session(BashAction(command="psql -U username -d database", session_id=session_id))
   ```

5. **Node.js REPL**
   ```python
   await runtime.run_in_session(BashAction(command="node", session_id=session_id))
   ```

6. **Python REPL**
   ```python
   await runtime.run_in_session(BashAction(command="python", session_id=session_id))
   ```

7. **MongoDB Shell**
   ```python
   await runtime.run_in_session(BashAction(command="mongosh", session_id=session_id))
   ```

8. **Vim** - Text editor
   ```python
   await runtime.run_in_session(BashAction(command="vim myfile.txt", session_id=session_id))
   ```

9. **Docker Interactive Shell**
   ```python
   await runtime.run_in_session(BashAction(command="docker exec -it container_name bash", session_id=session_id))
   ```

10. **Redis CLI**
    ```python
    await runtime.run_in_session(BashAction(command="redis-cli", session_id=session_id))
    ```

11. **htop** - Interactive process viewer
    ```python
    await runtime.run_in_session(BashAction(command="htop", session_id=session_id))
    ```

12. **R Interactive Environment**
    ```python
    await runtime.run_in_session(BashAction(command="R", session_id=session_id))
    ```

13. **Julia REPL**
    ```python
    await runtime.run_in_session(BashAction(command="julia", session_id=session_id))
    ```

14. **FTP Client**
    ```python
    await runtime.run_in_session(BashAction(command="ftp hostname", session_id=session_id))
    ```

15. **SQLite Interactive Shell**
    ```python
    await runtime.run_in_session(BashAction(command="sqlite3 mydatabase.db", session_id=session_id))
    ```

Each of these tools would remain interactive within the session, allowing you to send subsequent commands to them using the same `run_in_session` method.
