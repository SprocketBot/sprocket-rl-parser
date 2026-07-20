use boxcars::{NetworkParse, ParserBuilder};

const ANONYMIZED_NAME_REPLAY: &[u8] =
    include_bytes!("../test-files/973E29BA437C1AA2B54BC6AFE28BA0B3.replay");

#[test]
fn parses_network_frames_with_anonymized_player_names() {
    let replay = ParserBuilder::new(ANONYMIZED_NAME_REPLAY)
        .with_network_parse(NetworkParse::IgnoreOnError)
        .on_error_check_crc()
        .parse()
        .expect("replay should parse");

    let network_frames = replay
        .network_frames
        .expect("network parsing errors must not be silently downgraded to missing frames");

    assert_eq!(network_frames.frames.len(), 10_659);
}
