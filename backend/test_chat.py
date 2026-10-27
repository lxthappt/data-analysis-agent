from agent.agent import run

if __name__ == "__main__":
    q = input("请输入问题：")
    answer = run(q)
    print("\n=== 回答 ===\n")
    print(answer)