"""
Running loss parsing from Oryx for Ukrainian losses
"""
from src import loss_parser
from src import util


if __name__ == "__main__":
    args = util.parse_args()
    limit, limit_tag = "Attack On Europe: Documenting Ukrainian Equipment" \
                       " Losses During The Russian Invasion Of Ukraine", "a"
    content = util.HTMLFileContent(args.file).load().truncate_content(limit, limit_tag)
    ukr_losses = loss_parser.OryxLossParser().parse_losses(content())
    util.ParsedContent(ukr_losses).load().to_csv(args.output_file)
