import json
import argparse
import torch
import pandas as pd
from torch.optim import Adam
from torch.utils.data import DataLoader
from os import path, makedirs, getcwd
from sklearn.model_selection import train_test_split


from utils.seed import seed_everything
from utils.runner import AutoEncoderRunner
from basis.model import BasisAutoEncoder
from basis.dataset import BasisImageDataset
from basis.loss import Reconstruction


def parse_arguments():
    parser = argparse.ArgumentParser(description='Training AE for basis images')
    # for data
    parser.add_argument('--data-path', default='dataset/preprocess/mp_dataset_2020_03',
                        type=str, help='path to preprocessed data (relative path)')
    parser.add_argument('--csv-path', default='dataset/raw/data_2020_03_03.csv',
                        type=str, help='path to csv data (relative path)')
    parser.add_argument('--out-dir', '-o', default='result/basis',
                        type=str, help='path for output directory')
    # usual setting
    parser.add_argument('--train-ratio', default=0.9, type=float,
                        help='percentage of train data to be loaded (0.9)')
    parser.add_argument('--test-ratio', default=0.1, type=float,
                        help='percentage of test data to be loaded (0.1)')

    # for model
    parser.add_argument('--z-size', default=200, type=int, help='size for latent variable (200)')

    # for learning
    parser.add_argument('--gpu', '-g', action='store_true',
                        help='using gpu during training')
    parser.add_argument('--epochs', '-e', default=21, type=int,
                        help='number of total epochs to run (21)')
    parser.add_argument('--batch-size', '-b', default=24, type=int,
                        help='mini-batch size (24)')
    parser.add_argument('--learning-rate', '-lr', default=0.0003, type=float,
                        help='initial learning rate (default: 0.0003')
    parser.add_argument('--optim', choices=['SGD', 'Adam'], default='Adam',
                        help='choose an optimizer, SGD or Adam, (default: Adam)')
    parser.add_argument('--seed', default=1234, type=int, help='seed value (default: 1234)')

    return parser.parse_args()


def main():
    # get args
    args = parse_arguments()

    # make output directory
    out_dir = args.out_dir
    out_dir_path = path.normpath(path.join(getcwd(), out_dir))
    makedirs(out_dir_path, exist_ok=True)
    # save the parameter
    with open(path.join(out_dir_path, 'params.json'), mode="w") as f:
        json.dump(args.__dict__, f, indent=4)

    # setup
    seed_everything(args.seed)
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    # load raw dataset
    csv_path = path.normpath(path.join(getcwd(), args.csv_path))
    table_data = pd.read_csv(csv_path, index_col=False)
    mp_ids = table_data['material_id'].values
    data_dir = path.normpath(path.join(getcwd(), args.data_path))
    table = pd.read_csv(path.join(data_dir, 'basis_image.csv'))
    mp_ids = list(set(table['mp_id'].values))

    # split
    train_ids, test_ids = train_test_split(mp_ids, test_size=args.test_ratio, random_state=args.seed)
    # setup data loader
    data_dir = path.normpath(path.join(getcwd(), args.data_path))
    train_dataset = BasisImageDataset(train_ids, data_dir)
    test_dataset = BasisImageDataset(test_ids, data_dir)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    valid_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    loaders = {'train': train_loader, 'valid': valid_loader}

    # train
    model = BasisAutoEncoder(z_size=args.z_size)
    model = model.to(device)
    optimizer = Adam(model.parameters(), lr=args.learning_rate)
    criterion = Reconstruction()
    scheduler = None

    # runner
    runner = AutoEncoderRunner(device=device)
    # model training
    runner.train(model=model, criterion=criterion, optimizer=optimizer, scheduler=scheduler,
                 loaders=loaders, logdir=args.out_dir, num_epochs=args.epochs)


if __name__ == '__main__':
    main()
