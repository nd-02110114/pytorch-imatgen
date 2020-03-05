import torch
import functools
import numpy as np
import pandas as pd
from os import path
from torch.utils.data import Dataset


class CellImageDataset(Dataset):
    """
    Wrapper for a dataset
    """

    def __init__(self, mp_ids, data_dir):
        """
        Args:
            mp_ids (List): materials ids for cell images
            data_dir (string): path for preprocessed data
        """
        self.data_dir = data_dir
        table = pd.read_csv(path.join(data_dir, 'cell_image.csv'))
        self.table = table[table['mp_id'].isin(mp_ids)]

    def __len__(self):
        return len(self.table)

    @functools.lru_cache(maxsize=None)  # Cache loaded structures
    def __getitem__(self, idx):
        image_name = self.table.iloc[idx]['image_name']
        image = np.load(path.join(self.data_dir, 'cell_image', '{}.npy'.format(image_name)))
        image = np.transpose(image, (3, 0, 1, 2))
        return torch.tensor(image, dtype=torch.float)
