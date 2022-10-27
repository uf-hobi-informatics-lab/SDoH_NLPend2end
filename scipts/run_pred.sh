#run prediction from notes
#git clone https://github.com/uf-hobi-informatics-lab/ClinicalTransformerRelationExtraction.git
#git clone https://github.com/uf-hobi-informatics-lab/ClinicalTransformerNER.git
#git clone https://github.com/uf-hobi-informatics-lab/NLPreprocessing.git

while getopts :i:d:n:c: flag
do
    case "${flag}" in
        i) input_dir=${OPTARG};;
        c) cuda=${OPTARG};;
    esac
done
echo "Input dir: $input_dir";
echo "CUDA used: $cuda";

output_dir=../results
output_name=bio3


mkdir $output_dir
export CUDA_VISIBLE_DEVICES=$cuda
eva_dir=input_dir
python3 ./run_ner.py $input_dir $output_name
input_dir_2=../temp/encoding_txt/
python3 ../ClinicalTransformerNER/src/run_transformer_batch_prediction.py \
      --model_type bert \
      --pretrained_model ../models/ner_bert \
      --raw_text_dir $input_dir_2 \
      --preprocessed_text_dir ../temp/${output_name} \
      --output_dir ../temp/out/${output_name} \
      --max_seq_length 128 \
      --do_lower_case \
      --eval_batch_size 8 \
      --log_file ../logs/log_ner_bio.txt\
      --do_format 1 \
      --do_copy \
      --data_has_offset_information


python3 ./make_relation.py $input_dir $output_name


bz=4
epn=3
sc=2
dfmm=0
model_type=bert
pm=bert-large
data_dir_re=../temp/${output_name}_aio_th1
nmd=../models/re_bert
pof=../temp/predictions_${output_name}.txt
log=../logs/log_re_${output_name}.txt

# if ls $data_dir_re  | wc -l ==0
# if [ "$data_dir_re" -ne 0 ]; then
#     echo 'array is not empty'
if [ -f "$data_dir_re/test.tsv" ]; then
    echo "$data_dir_re exists."

python3 ../ClinicalTransformerRelationExtraction/src/relation_extraction.py \
                --model_type $model_type \
                --data_format_mode $dfmm \
                --classification_scheme $sc \
                --pretrained_model $pm \
                --data_dir $data_dir_re \
                --new_model_dir $nmd \
                --predict_output_file $pof \
                --overwrite_model_dir \
                --seed 13 \
                --max_seq_length 512 \
                --num_core 10 \
                --cache_data \
                --do_predict \
                --do_lower_case \
                --train_batch_size $bz \
                --eval_batch_size $bz \
                --learning_rate 1e-5 \
                --num_train_epochs $epn \
                --gradient_accumulation_steps 1 \
                --do_warmup \
                --warmup_ratio 0.1 \
                --weight_decay 0 \
                --max_num_checkpoints 0 \
                --log_file $log

mkdir ${output_dir}/result
mkdir ${output_dir}/result/eval
mkdir ${output_dir}/result/RE
#
edr=../temp/out/${output_name}_formatted_output
pod=${output_dir}/result/RE/${output_name}_relation_predicted_results
python3 ../ClinicalTransformerRelationExtraction/src/data_processing/post_processing.py \
                --mode mul \
                --predict_result_file $pof \
                --entity_data_dir $edr \
                --test_data_file ${data_dir_re}/test.tsv \
                --brat_result_output_dir $pod\
                --log_file $log

python brat_eval.py --f1 $eva_dir --f2 $pod >> ${output_dir}/eval_result.txt #compare the eva_dir with RE result
echo output file location $pod
else
echo no relation candidate pairs
python brat_eval.py --f1 $eva_dir --f2 ../temp/out/${output_name}_formatted_output >> ${output_dir}/eval_result.txt #compare eva_dir with NER result


fi
