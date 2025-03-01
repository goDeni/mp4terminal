extern crate argparse;

use argparse::{ArgumentParser, Store};
use std::fs::File;
use std::path::{Path, PathBuf};

struct Args {
    path: PathBuf,
}

fn parse_args() -> Args {
    let mut path = String::new();
    {
        let mut parser = ArgumentParser::new();
        parser
            .refer(&mut path)
            .required()
            .add_argument("file", Store, "Vieo file path");

        parser.parse_args_or_exit();
    }
    Args {
        path: Path::new(path.as_str()).to_path_buf(),
    }
}

fn main() {
    let args = parse_args();
    if !args.path.is_file() {
        println!("File '{}' doesn't exists", args.path.to_str().unwrap());
        return;
    }

    File::open(args.path).expect("Unable to open file");
}
