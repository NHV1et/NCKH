import pandas as pd
from sklearn.model_selection import train_test_split


def load_dataset(path):
    df = pd.read_csv(path)

    X = df.drop(columns=["Domain", "Label"])
    y = df["Label"]

    return train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )