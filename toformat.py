import sys


def main():
    f = open("properQuestions.txt", "a")
    number = 1
    for line in sys.stdin:
        if line == "\n":
            break
        f.write(str(number) + "  " + line)
        number += 1
    f.close()


if __name__ == "__main__":
    main()
