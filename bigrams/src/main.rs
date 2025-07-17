use flate2::read::GzDecoder;
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufRead, BufReader, BufWriter, Write};

use std::sync::{Arc, Mutex};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load all words from filtered words file
    println!("Loading words...");
    let mut all_words = std::collections::HashSet::new();
    let file = File::open("../4_filtered_words.txt")?;
    let reader = BufReader::new(file);

    for line in reader.lines() {
        let word = line?.trim().to_string();
        if !word.is_empty() {
            all_words.insert(word);
        }
    }

    println!("Loaded words");

    // Get list of files in 2grams directory
    let bigrams_dir = "../2grams";
    let mut files: Vec<_> = fs::read_dir(bigrams_dir)?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().ok().map_or(false, |ft| ft.is_file()))
        .map(|entry| entry.path())
        .collect();

    files.sort(); // For consistent ordering

    // Shared bigram counts protected by mutex
    let bigram_counts = Arc::new(Mutex::new(HashMap::<(String, String), u64>::new()));

    // Process files in parallel
    files.par_iter().enumerate().for_each(|(_i, file_path)| {
        if let Some(filename) = file_path.file_name().and_then(|n| n.to_str()) {
            println!("{}", filename);

            if let Ok(file) = File::open(file_path) {
                let decoder = GzDecoder::new(file);
                let reader = BufReader::new(decoder);

                let mut local_counts = HashMap::<(String, String), u64>::new();

                for (j, line) in reader.lines().enumerate() {
                    if let Ok(line) = line {
                        let parts: Vec<&str> = line.trim().split('\t').collect();
                        if parts.len() >= 4 {
                            let ngram = parts[0];
                            let year: i32 = parts[1].parse().unwrap_or(0);
                            let volume_count: u64 = parts[3].parse().unwrap_or(0);

                            let ngram_parts: Vec<&str> = ngram.split_whitespace().collect();
                            if ngram_parts.len() >= 2 {
                                let word1 =
                                    ngram_parts[0].split('_').next().unwrap_or("").to_string();
                                let word2 =
                                    ngram_parts[1].split('_').next().unwrap_or("").to_string();

                                if year < 1950 || word1.is_empty() {
                                    continue;
                                }

                                if all_words.contains(&word1) && all_words.contains(&word2) {
                                    *local_counts.entry((word1, word2)).or_insert(0) +=
                                        volume_count;
                                }
                            }
                        }

                        if j % 1_000_000 == 0 {
                            println!("{}", j);
                        }
                    }
                }

                // Merge local counts into global counts
                let mut global_counts = bigram_counts.lock().unwrap();
                for ((word1, word2), count) in local_counts {
                    *global_counts.entry((word1, word2)).or_insert(0) += count;
                }
            }
        }
    });

    // Extract final counts
    let final_counts = bigram_counts.lock().unwrap();

    // Sort bigrams by count (descending)
    let mut sorted_bigrams: Vec<_> = final_counts.iter().collect();
    sorted_bigrams.sort_by(|a, b| b.1.cmp(a.1));

    // Write to all_bigrams.txt
    let output_file = File::create("../all_bigrams.txt")?;
    let mut writer = BufWriter::new(output_file);

    for ((word1, word2), _count) in sorted_bigrams.iter() {
        writeln!(writer, "{} {}", word1, word2)?;
    }

    writer.flush()?;

    println!("Processing complete. Results written to all_bigrams.txt");

    Ok(())
}
