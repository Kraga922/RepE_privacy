import pandas as pd
import numpy as np
import random
from transformers import PreTrainedTokenizer
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.colors import LinearSegmentedColormap

def privacy_function_dataset(data_path: str, tokenizer: PreTrainedTokenizer, user_tag: str = "", assistant_tag: str = "", seed: int = 0) -> (list, list):
    """
    Processes privacy data to create training and testing datasets based on privacy sensitivity.

    Args:
    - data_path (str): Path to the CSV containing the privacy data.
    - tokenizer (PreTrainedTokenizer): Tokenizer to tokenize statements.
    - user_tag (str): Instruction template.
    - assistant_tag (str): Instruction template user tag.
    - seed (int): Random seed for reproducibility.

    Returns:
    - Tuple containing train and test data.
    """

    # Setting the seed for reproducibility
    random.seed(seed)

    # Load the data
    df = pd.read_csv(data_path)
    
    # Assuming privacy labels: 1 = privacy-sensitive, 0 = not privacy-sensitive
    # You may need to adjust this based on your actual label scheme
    privacy_sensitive_statements = df[df['label'] == 1]['statement'].values.tolist()
    privacy_insensitive_statements = df[df['label'] == 0]['statement'].values.tolist()

    template_str = "Pretend you're {type} person responding to questions about privacy and data sensitivity."
    privacy_aware_statements = []
    privacy_dismissive_statements = []

    # Process privacy-sensitive statements
    for statement in privacy_sensitive_statements:
        tokens = tokenizer.tokenize(statement)
        
        for idx in range(1, len(tokens) - 5):
            truncated_tokens = tokens[:idx]
            truncated_statement = tokenizer.convert_tokens_to_string(truncated_tokens)

            privacy_aware_statements.append(f"{user_tag} {template_str.format(type='a privacy-conscious')} {assistant_tag} " + truncated_statement)
            privacy_dismissive_statements.append(f"{user_tag} {template_str.format(type='a privacy-dismissive')} {assistant_tag} " + truncated_statement)

    # Process privacy-insensitive statements
    for statement in privacy_insensitive_statements:
        tokens = tokenizer.tokenize(statement)
        
        for idx in range(1, len(tokens) - 5):
            truncated_tokens = tokens[:idx]
            truncated_statement = tokenizer.convert_tokens_to_string(truncated_tokens)

            # For insensitive statements, we might want different handling
            # Here, we'll treat them as examples where privacy-awareness is less critical
            privacy_aware_statements.append(f"{user_tag} {template_str.format(type='a privacy-conscious')} {assistant_tag} " + truncated_statement)
            privacy_dismissive_statements.append(f"{user_tag} {template_str.format(type='a privacy-dismissive')} {assistant_tag} " + truncated_statement)

    # Create training data
    ntrain = 512
    combined_data = [[privacy_aware, privacy_dismissive] for privacy_aware, privacy_dismissive in zip(privacy_aware_statements, privacy_dismissive_statements)]
    train_data = combined_data[:ntrain]

    train_labels = []
    for d in train_data:
        privacy_aware_s = d[0]  # The privacy-aware response
        random.shuffle(d)
        train_labels.append([s == privacy_aware_s for s in d])
    
    train_data = np.concatenate(train_data).tolist()

    # Create test data
    reshaped_data = np.array([[privacy_aware, privacy_dismissive] for privacy_aware, privacy_dismissive in zip(privacy_aware_statements[:-1], privacy_dismissive_statements[1:])]).flatten()
    test_data = reshaped_data[ntrain:ntrain*2].tolist()

    print(f"Train data: {len(train_data)}")
    print(f"Test data: {len(test_data)}")

    return {
        'train': {'data': train_data, 'labels': train_labels},
        'test': {'data': test_data, 'labels': [[1,0]] * len(test_data)}
    }


# Alternative version if you want to handle multi-level privacy sensitivity
def privacy_function_dataset_multilevel(data_path: str, tokenizer: PreTrainedTokenizer, user_tag: str = "", assistant_tag: str = "", seed: int = 0, sensitivity_threshold: int = 2) -> (list, list):
    """
    Processes privacy data with multiple sensitivity levels.

    Args:
    - data_path (str): Path to the CSV containing the privacy data.
    - tokenizer (PreTrainedTokenizer): Tokenizer to tokenize statements.
    - user_tag (str): Instruction template.
    - assistant_tag (str): Instruction template user tag.
    - seed (int): Random seed for reproducibility.
    - sensitivity_threshold (int): Threshold above which items are considered sensitive.

    Returns:
    - Tuple containing train and test data.
    """

    # Setting the seed for reproducibility
    random.seed(seed)

    # Load the data
    df = pd.read_csv(data_path)
    
    # Convert sensitivity ratings to binary (sensitive vs not sensitive)
    # Adjust the threshold based on your rating scale
    df['is_sensitive'] = (df['label'] > sensitivity_threshold).astype(int)
    
    sensitive_statements = df[df['is_sensitive'] == 1]['statement'].values.tolist()
    insensitive_statements = df[df['is_sensitive'] == 0]['statement'].values.tolist()

    # Combine all statements for processing
    all_statements = sensitive_statements + insensitive_statements
    all_labels = [1] * len(sensitive_statements) + [0] * len(insensitive_statements)

    template_str = "Pretend you're {type} person responding to questions about privacy and data sensitivity."
    privacy_aware_statements = []
    privacy_dismissive_statements = []

    # Process all statements
    for statement, is_sensitive in zip(all_statements, all_labels):
        tokens = tokenizer.tokenize(statement)
        
        for idx in range(1, len(tokens) - 5):
            truncated_tokens = tokens[:idx]
            truncated_statement = tokenizer.convert_tokens_to_string(truncated_tokens)

            privacy_aware_statements.append(f"{user_tag} {template_str.format(type='a privacy-conscious')} {assistant_tag} " + truncated_statement)
            privacy_dismissive_statements.append(f"{user_tag} {template_str.format(type='a privacy-dismissive')} {assistant_tag} " + truncated_statement)

    # Create training data
    ntrain = 512
    combined_data = [[privacy_aware, privacy_dismissive] for privacy_aware, privacy_dismissive in zip(privacy_aware_statements, privacy_dismissive_statements)]
    train_data = combined_data[:ntrain]

    train_labels = []
    for d in train_data:
        privacy_aware_s = d[0]
        random.shuffle(d)
        train_labels.append([s == privacy_aware_s for s in d])
    
    train_data = np.concatenate(train_data).tolist()

    # Create test data
    reshaped_data = np.array([[privacy_aware, privacy_dismissive] for privacy_aware, privacy_dismissive in zip(privacy_aware_statements[:-1], privacy_dismissive_statements[1:])]).flatten()
    test_data = reshaped_data[ntrain:ntrain*2].tolist()

    print(f"Train data: {len(train_data)}")
    print(f"Test data: {len(test_data)}")

    return {
        'train': {'data': train_data, 'labels': train_labels},
        'test': {'data': test_data, 'labels': [[1,0]] * len(test_data)}
    }

def plot_detection_results(input_ids, rep_reader_scores_dict, THRESHOLD, start_answer_token=":"):

    cmap=LinearSegmentedColormap.from_list('rg',["r", (255/255, 255/255, 224/255), "g"], N=256)
    colormap = cmap

    # Define words and their colors
    words = [token.replace('▁', ' ') for token in input_ids]

    # Create a new figure
    fig, ax = plt.subplots(figsize=(12.8, 10), dpi=200)

    # Set limits for the x and y axes
    xlim = 1000
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, 10)

    # Remove ticks and labels from the axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Starting position of the words in the plot
    x_start, y_start = 1, 8
    y_pad = 0.3
    # Initialize positions and maximum line width
    x, y = x_start, y_start
    max_line_width = xlim

    y_pad = 0.3
    word_width = 0

    iter = 0

    selected_concepts = ["privacy"]
    norm_style = ["mean"]
    selection_style = ["neg"]

    for rep, s_style, n_style in zip(selected_concepts, selection_style, norm_style):

        rep_scores = np.array(rep_reader_scores_dict[rep])
        mean, std = np.median(rep_scores), rep_scores.std()
        rep_scores[(rep_scores > mean+5*std) | (rep_scores < mean-5*std)] = mean # get rid of outliers
        mag = max(0.3, np.abs(rep_scores).std() / 10)
        min_val, max_val = -mag, mag
        norm = Normalize(vmin=min_val, vmax=max_val)

        if "mean" in n_style:
            rep_scores = rep_scores - THRESHOLD # change this for threshold
            rep_scores = rep_scores / np.std(rep_scores[5:])
            rep_scores = np.clip(rep_scores, -mag, mag)
        if "flip" in n_style:
            rep_scores = -rep_scores
        
        rep_scores[np.abs(rep_scores) < 0.0] = 0

        # ofs = 0
        # rep_scores = np.array([rep_scores[max(0, i-ofs):min(len(rep_scores), i+ofs)].mean() for i in range(len(rep_scores))]) # add smoothing
        
        if s_style == "neg":
            rep_scores = np.clip(rep_scores, -np.inf, 0)
            rep_scores[rep_scores == 0] = mag
        elif s_style == "pos":
            rep_scores = np.clip(rep_scores, 0, np.inf)


        # Initialize positions and maximum line width
        x, y = x_start, y_start
        max_line_width = xlim
        started = False
            
        for word, score in zip(words[5:], rep_scores[5:]):

            if start_answer_token in word:
                started = True
                continue
            if not started:
                continue
            
            color = colormap(norm(score))

            # Check if the current word would exceed the maximum line width
            if x + word_width > max_line_width:
                # Move to next line
                x = x_start
                y -= 3

            # Compute the width of the current word
            text = ax.text(x, y, word, fontsize=13)
            word_width = text.get_window_extent(fig.canvas.get_renderer()).transformed(ax.transData.inverted()).width
            word_height = text.get_window_extent(fig.canvas.get_renderer()).transformed(ax.transData.inverted()).height

            # Remove the previous text
            if iter:
                text.remove()

            # Add the text with background color
            text = ax.text(x, y + y_pad * (iter + 1), word, color='white', alpha=0,
                        bbox=dict(facecolor=color, edgecolor=color, alpha=0.8, boxstyle=f'round,pad=0', linewidth=0),
                        fontsize=13)
            
            # Update the x position for the next word
            x += word_width + 0.1
        
        iter += 1


def plot_lat_scans(input_ids, rep_reader_scores_dict, layer_slice):
    for rep, scores in rep_reader_scores_dict.items():

        start_tok = input_ids.index('Ġsocial')
        print(start_tok, np.array(scores).shape)
        # standardized_scores = np.array(scores)[start_tok:start_tok+40,layer_slice]
        # print(standardized_scores.shape)

        #KA

        score_array = np.array(scores)
        
        # print(f"start_tok: {start_tok}, end_tok: {start_tok+40}")
        # print(f"token range shape: {score_array[start_tok:start_tok+40].shape}")
        # print(f"layer_slice: {layer_slice}")


        print("Shape before slicing:", score_array.shape)
        standardized_scores = score_array[start_tok:start_tok+40, layer_slice]
        print("Shape after slicing:", standardized_scores.shape)


        bound = np.mean(standardized_scores) + np.std(standardized_scores)
        bound = 2.3

        # standardized_scores = np.array(scores)
        
        # threshold = 0
        # standardized_scores[np.abs(standardized_scores) < threshold] = 1
        standardized_scores = standardized_scores.clip(-bound, bound)

        #KA        
        print("Standardized scores min/max:", standardized_scores.min(), standardized_scores.max())

        # threshold = 0.01  # or some small positive value
        # standardized_scores[np.abs(standardized_scores) < threshold] = 0
        
        cmap = 'coolwarm'

        fig, ax = plt.subplots(figsize=(5, 4), dpi=200)
        sns.heatmap(-standardized_scores.T, cmap=cmap, linewidth=0.5, annot=False, fmt=".3f", vmin=-bound, vmax=bound)
        ax.tick_params(axis='y', rotation=0)

        ax.set_xlabel("Token Position")#, fontsize=20)
        ax.set_ylabel("Layer")#, fontsize=20)

        # x label appear every 5 ticks

        ax.set_xticks(np.arange(0, len(standardized_scores), 5)[1:])
        ax.set_xticklabels(np.arange(0, len(standardized_scores), 5)[1:])#, fontsize=20)
        ax.tick_params(axis='x', rotation=0)

        ax.set_yticks(np.arange(0, len(standardized_scores[0]), 5)[1:])
        ax.set_yticklabels(np.arange(20, len(standardized_scores[0])+20, 5)[::-1][1:])#, fontsize=20)
        ax.set_title("LAT Neural Activity")#, fontsize=30)
    plt.show()

