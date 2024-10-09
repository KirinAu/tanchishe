import pygame
import random
import numpy as np
from collections import defaultdict
import dill



def default_q_value():
    return np.zeros(4)
Q = defaultdict(default_q_value)


# 在游戏结束或定时保存 Q 表
def save_q_table(q_table, filename='q_table3.dill'):
    with open(filename, 'wb') as handle:
        dill.dump(q_table, handle)

# 在游戏开始时加载 Q 表
def load_q_table(filename='q_table3.dill'):
    try:
        with open(filename, 'rb') as handle:
            return dill.load(handle)
    except FileNotFoundError:
        print("Q-table file not found, starting with a new table.")
        return defaultdict(lambda: np.zeros(4))  # 返回一个新的 Q 表

# 定义颜色
white = (255, 255, 255)
black = (0, 0, 0)
red = (213, 50, 80)
green = (0, 255, 0)
blue = (50, 153, 213)
gametimes = 0

snake_head_x = 100
snake_head_y = 100
snake_block_size = 10
snake_length = 1
epsilon = 0.1
alpha = 0.1  # 学习率
gamma = 0.9  # 折扣因子

# 初始化pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))  # 主窗口大小
pygame.display.set_caption("贪吃蛇学习制作")  # 主窗口标题
clock = pygame.time.Clock()  # 创建一个时钟对象
snake_speed = 60  # 蛇的速度
snake_list = []  # 蛇身列表

snake_head = red
snake_body = white
food_color = green


def create_snake(snake_block_size, snake_list):
    for x in snake_list:
        pygame.draw.rect(screen, snake_body, [x[0], x[1], snake_block_size, snake_block_size])


def display_score(score):
    font = pygame.font.SysFont(None, 35)
    score_text = font.render("Score: " + str(score), True, white)
    screen.blit(score_text, [10, 10])  # 在主窗口中显示分数


def check_danger(snake_head_x, snake_head_y, snake_list):
    danger_left = (snake_head_x - snake_block_size < 0) or ([snake_head_x - snake_block_size, snake_head_y] in snake_list)
    danger_right = (snake_head_x + snake_block_size >= 800) or ([snake_head_x + snake_block_size, snake_head_y] in snake_list)
    danger_up = (snake_head_y - snake_block_size < 0) or ([snake_head_x, snake_head_y - snake_block_size] in snake_list)
    danger_down = (snake_head_y + snake_block_size >= 600) or ([snake_head_x, snake_head_y + snake_block_size] in snake_list)

    return (danger_left, danger_right, danger_up, danger_down)


def get_state(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list):
    # 简化状态表示, 仅考虑方向和危险性, 或者离散化坐标
    food_dir_x = 'right' if food_x > snake_head_x else 'left' if food_x < snake_head_x else 'same'
    food_dir_y = 'down' if food_y > snake_head_y else 'up' if food_y < snake_head_y else 'same'
    danger = check_danger(snake_head_x, snake_head_y, snake_list)
    return (food_dir_x, food_dir_y, direction, danger)


def choose_action(state, epsilon):
    if random.random() < epsilon:
        return random.randint(0, 3)
    else:
        return np.argmax(Q[state])


def step(action):
    global snake_head_x, snake_head_y, snake_list, food_x, food_y, snake_length, direction

    directions_map = {
        'UP': (0, -snake_block_size),
        'DOWN': (0, snake_block_size),
        'LEFT': (-snake_block_size, 0),
        'RIGHT': (snake_block_size, 0)
    }

    # 防止蛇直接掉头
    valid_actions = {
        'UP': [0, 2, 3],  # Can't go DOWN
        'DOWN': [1, 2, 3],  # Can't go UP
        'LEFT': [0, 1, 2],  # Can't go RIGHT
        'RIGHT': [0, 1, 3]  # Can't go LEFT
    }

    if action not in valid_actions[direction]:
        # 如果动作不合法，选择一个合法动作或者保持当前方向
        action = [a for a in valid_actions[direction] if a != action][0] if valid_actions[direction] else action

    # 更新方向
    direction = list(directions_map.keys())[action]

    # 获取新的移动向量并移动蛇头
    x_change, y_change = directions_map[direction]
    snake_head_x += x_change
    snake_head_y += y_change

    # 检查是否越界
    if (snake_head_x < 0 or snake_head_x >= 800 or snake_head_y < 0 or snake_head_y >= 600):
        return get_state(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list), -10000, True

    # 更新蛇身，先添加蛇头
    snake_list.append([snake_head_x, snake_head_y])

    # 检查是否与自身相撞
    if [snake_head_x, snake_head_y] in snake_list[:-1]:
        return get_state(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list), -10000, True

    # 检查是否吃到食物
    if snake_head_x == food_x and snake_head_y == food_y:
        snake_length += 1
        food_x, food_y = generate_food()  # 生成新的食物位置
        while [food_x, food_y] in snake_list:  # 确保新的食物不与蛇身重叠
            food_x, food_y = generate_food()
        return get_state(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list), 1000, False

    # 如果没有吃到食物，保持蛇身长度
    if len(snake_list) > snake_length:
        del snake_list[0]

    direction_score = should_turn_towards_food(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list)
    reward = -10  # 基础移动惩罚

    return get_state(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list), reward, False



def generate_food():
    while True:
        food_x = round(random.randrange(0, 800 - snake_block_size) / 10.0) * 10.0
        food_y = round(random.randrange(0, 600 - snake_block_size) / 10.0) * 10.0
        if [food_x, food_y] not in snake_list:  # 确保食物不在蛇身上
            return food_x, food_y


def update_q_table(state, action, reward, next_state, alpha, gamma):

    best_action = np.argmax(Q[next_state])
    td_target = reward + gamma * Q[next_state][best_action]
    td_error = td_target - Q[state][action]
    Q[state][action] += alpha * td_error


def reset_game():
    global snake_head_x, snake_head_y, snake_list, food_x, food_y, snake_length, direction

    # 初始化蛇头位置到屏幕中心
    snake_head_x = screen.get_width() // 2
    snake_head_y = screen.get_height() // 2

    snake_list = [[snake_head_x, snake_head_y]]  # 初始化蛇身只包含头部
    food_x, food_y = generate_food()
    while [food_x, food_y] in snake_list:  # 确保食物不在蛇身上
        food_x, food_y = generate_food()
    snake_length = 1
    direction = 'RIGHT'  # 初始方向设置为右


    return get_state(snake_head_x, snake_head_y, food_x, food_y, direction, snake_list)


def gameloop():
    global snake_length, epsilon, gametimes  # 确保epsilon是全局的，以在训练过程中衰减

    pre_score = 0
    while True:
        gametimes += 1
        state = reset_game()
        total_reward = 0
        episode = 0

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            action = choose_action(state, epsilon)
            next_state, reward, done = step(action)
            update_q_table(state, action, reward, next_state, alpha, gamma)
            state = next_state
            total_reward += reward

            if done:
                episode += 1
                currentscore = snake_length - 1
                if currentscore > pre_score:
                    total_reward += 1000
                if currentscore < pre_score:
                    total_reward -= 2000
                print(f"gametime:{gametimes}, Episode: {episode}, Score: {snake_length - 1}, Total Reward: {total_reward}, Q-values for current state: {Q[state]}, Current state: {state}")
                # 可以在这里添加epsilon衰减逻辑
                if epsilon > 0.01:  # 假设的最小探索率
                    epsilon *= 0.995  # 每次衰减epsilon，使探索减少，利用增多

                # 不需要等待玩家输入，直接进入下一个训练回合
                break

            screen.fill(black)
            pygame.draw.rect(screen, food_color, [food_x, food_y, snake_block_size, snake_block_size])
            create_snake(snake_block_size, snake_list)
            display_score(snake_length - 1)
            pygame.display.update()
            clock.tick(snake_speed)
            save_q_table(Q)

        # 当done为True时，循环会break到这里，开始新一轮训练


def should_turn_towards_food(snake_head_x, snake_head_y, food_x, food_y, current_direction, snake_list):
    # 计算到食物的方向向量
    to_food_x = food_x - snake_head_x
    to_food_y = food_y - snake_head_y

    # 定义蛇移动的方向向量
    directions = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'LEFT': (-1, 0),
        'RIGHT': (1, 0)
    }
    move_x, move_y = directions.get(current_direction, (0, 0))

    # 使用点积判断方向
    dot_product = move_x * to_food_x + move_y * to_food_y

    # 如果点积大于某阈值，说明方向大致对准，返回1；否则返回-1。
    # 这里使用0.5作为阈值，你可以根据需要调整
    if dot_product > 0.5:
        return 1  # 方向大致对准，加分
    else:
        return -1  # 方向偏离，减分


def main():
    global epsilon, alpha, gamma  # 将 alpha 和 gamma 声明为全局变量
    epsilon = 0.1
    alpha = 0.1  # 学习率
    gamma = 0.9  # 折扣因子
    episodes = 5000

    for episode in range(episodes):
        state = reset_game()  # 初始化游戏
        done = False

        while not done:
            action = choose_action(state, epsilon)
            next_state, reward, done = step(action)
            update_q_table(state, action, reward, next_state, alpha, gamma)
            state = next_state

        # Epsilon 衰减
        if episode % 100 == 0:
            epsilon = max(epsilon * 0.99, 0.01)  # 确保 epsilon 不低于 0.01
gameloop()  # 在训练后开始游戏循环


if __name__ == "__main__":
    Q = load_q_table()
    main()