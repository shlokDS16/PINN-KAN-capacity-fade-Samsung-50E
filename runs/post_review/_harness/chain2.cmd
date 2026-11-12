@echo off
"C:\Users\Shlok\Downloads\PINN KAN battery paper\.venv\Scripts\python.exe" -P "C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\_harness\run_exp.py" item5_cap 6 < NUL > "C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\_harness\item5_rerun.log" 2>&1
"C:\Users\Shlok\Downloads\PINN KAN battery paper\.venv\Scripts\python.exe" -P "C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\_harness\nc2.py" run 11 1-10 < NUL > "C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\_harness\nc2_draws1_10.log" 2>&1
